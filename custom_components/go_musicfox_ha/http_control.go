package remote_control

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"sync"
	"time"

	"github.com/go-musicfox/go-musicfox/internal/types"
)

// PlayerStatus contains the current player status
type PlayerStatus struct {
	SongTitle      string        `json:"song_title"`
	Artist         string        `json:"artist"`
	IsPlaying      bool          `json:"is_playing"`
	PlayMode       uint8         `json:"play_mode"`
	SongDuration   time.Duration `json:"song_duration"`
	PlaybackPlayed time.Duration `json:"playback_played"`
	Lyric          string        `json:"lyric"`
	IsLoggedIn     bool          `json:"is_logged_in"`
}

// PlayerController player controller interface
type PlayerController interface {
	SetPlayMode(types.Mode) error
	Play()
	Pause()
	Next()
	Previous()
	NextPlayMode()
	ActivateIntelligentMode() error
	GetStatus() PlayerStatus
	Rerender()
}

// HTTPController http controller
type HTTPController struct {
	playerController PlayerController
	sseClients       map[chan string]struct{}
	mu               sync.Mutex
}

// NewHTTPController new http controller
func NewHTTPController(playerController PlayerController) *HTTPController {
	return &HTTPController{
		playerController: playerController,
		sseClients:       make(map[chan string]struct{}),
	}
}

// Run run http server
func (c *HTTPController) Run(port int) {
	slog.Info("HTTP controller is running on", slog.Int("port", port))
	http.HandleFunc("/api/v1/command", c.commandHandler)
	http.HandleFunc("/api/v1/status", c.statusHandler)
	http.HandleFunc("/api/v1/events", c.sseHandler)
	go func() {
		if err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil); err != nil {
			slog.Error("http controller listen and serve failed", slog.Any("err", err))
		}
	}()
}

// BroadcastStatus broadcasts the current player status to all SSE clients.
func (c *HTTPController) BroadcastStatus(status PlayerStatus) {
	c.mu.Lock()
	defer c.mu.Unlock()

	jsonData, err := json.Marshal(status)
	if err != nil {
		slog.Error("Failed to marshal status for SSE broadcast", slog.Any("err", err))
		return
	}

	for clientChan := range c.sseClients {
		select {
		case clientChan <- string(jsonData):
		default:
			// Client channel is full, skip.
		}
	}
}

func (c *HTTPController) sseHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	clientChan := make(chan string, 1) // Buffered channel
	c.mu.Lock()
	c.sseClients[clientChan] = struct{}{}
	c.mu.Unlock()

	defer func() {
		c.mu.Lock()
		delete(c.sseClients, clientChan)
		c.mu.Unlock()
		close(clientChan)
	}()

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported!", http.StatusInternalServerError)
		return
	}

	// Send initial state immediately
	initialStatus := c.playerController.GetStatus()
	initialData, _ := json.Marshal(initialStatus)
	fmt.Fprintf(w, "data: %s\n\n", initialData)
	flusher.Flush()

	for {
		select {
		case data := <-clientChan:
			fmt.Fprintf(w, "data: %s\n\n", data)
			flusher.Flush()
		case <-r.Context().Done():
			return
		}
	}
}

func (c *HTTPController) statusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	status := c.playerController.GetStatus()
	resp, err := json.Marshal(status)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte(fmt.Sprintf(`{"status": "error", "message": "%s"}`, err.Error())))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(resp)
}

type command struct {
	Command string   `json:"command"`
	Args    []string `json:"args"`
}

func (c *HTTPController) commandHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	var cmd command
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(fmt.Sprintf(`{"status": "error", "message": "%s"}`, err.Error())))
		return
	}
	defer r.Body.Close()

	switch cmd.Command {
	case "set_play_mode":
		if len(cmd.Args) != 1 {
			w.WriteHeader(http.StatusBadRequest)
			_, _ = w.Write([]byte(`{"status": "error", "message": "invalid args"}`)) 
			return
		}
		var mode types.Mode
		switch cmd.Args[0] {
		case "ordered":
			mode = types.PmOrdered
		case "list_loop":
			mode = types.PmListLoop
		case "single_loop":
			mode = types.PmSingleLoop
		case "list_random":
			mode = types.PmListRandom
		case "inf_random":
			mode = types.PmInfRandom
		default:
			w.WriteHeader(http.StatusBadRequest)
			_, _ = w.Write([]byte(`{"status": "error", "message": "invalid play mode"}`)) 
			return
		}
		if err := c.playerController.SetPlayMode(mode); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_, _ = w.Write([]byte(fmt.Sprintf(`{"status": "error", "message": "%s"}`, err.Error())))
			return
		}
		c.playerController.Rerender() // Trigger UI refresh

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "play":
		c.playerController.Play()
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "pause":
		c.playerController.Pause()
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "next":
		c.playerController.Next()
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "previous":
		c.playerController.Previous()
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "next_play_mode":
		c.playerController.NextPlayMode()
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	case "activate_intelligent_mode":
		if err := c.playerController.ActivateIntelligentMode(); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_, _ = w.Write([]byte(fmt.Sprintf(`{"status": "error", "message": "%s"}`, err.Error())))
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status": "ok"}`)) 
	default:
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"status": "error", "message": "unknown command"}`)) 
	}
}
