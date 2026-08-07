package main

import (
	"fmt"
	"log"

	"github.com/sashko/go-uinput"
	"github.com/veandco/go-sdl2/sdl"
	"github.com/veandco/go-sdl2/ttf"
)

func main() {

	keyboard, kerr := uinput.CreateKeyboard()
	if kerr != nil {
		panic(kerr)
	}
	defer keyboard.Close()

	err := sdl.Init(sdl.INIT_VIDEO)
	if err != nil {
		log.Fatal(err)
	}
	defer sdl.Quit()

	if err := ttf.Init(); err != nil {
		log.Fatal(err)
	}
	defer ttf.Quit()

	window, _ := sdl.CreateWindow(
		"kbd",
		0, // sdl.WINDOWPOS_CENTERED,
		0, // sdl.WINDOWPOS_CENTERED,
		1000, 400,
		sdl.WINDOW_SHOWN|
			sdl.WINDOW_ALWAYS_ON_TOP|
			sdl.WINDOW_POPUP_MENU|
			sdl.WINDOW_BORDERLESS,
		// sdl.WINDOW_FULLSCREEN_DESKTOP,
		// sdl.WINDOW_SKIP_TASKBAR,
	)

	go func() {
		for {
			window.Raise()
			sdl.Delay(300)
		}
	}()

	// sdl.SetHint(sdl.HINT_MOUSE_FOCUS_CLICKTHROUGH, "1")
	if err != nil {
		log.Fatal(err)
	}
	defer window.Destroy()

	renderer, err := sdl.CreateRenderer(window, -1, sdl.RENDERER_ACCELERATED)
	if err != nil {
		log.Fatal(err)
	}
	defer renderer.Destroy()

	// Load font - trying common system font paths
	font, err := ttf.OpenFont("DejaVuSansMono-Bold.ttf", 24)
	if err != nil {
		// Try alternative Linux font path
		font, err = ttf.OpenFont("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 24)
		if err != nil {
			// Try macOS font path
			font, err = ttf.OpenFont("/System/Library/Fonts/Helvetica.ttc", 24)
			if err != nil {
				log.Fatal("Could not load font:", err)
			}
		}
	}
	defer font.Close()

	/*
		type 0 = key write
		type 1 = action
		type 2 = command
	*/
	type Will struct {
		Type    uint8
		KeyCode int
		Action  string
	}

	keyMap := map[string]Will{

		"0":     Will{Type: 0, KeyCode: uinput.Key0},
		"1":     Will{Type: 0, KeyCode: uinput.Key1},
		"2":     Will{Type: 0, KeyCode: uinput.Key2},
		"3":     Will{Type: 0, KeyCode: uinput.Key3},
		"4":     Will{Type: 0, KeyCode: uinput.Key4},
		"5":     Will{Type: 0, KeyCode: uinput.Key5},
		"6":     Will{Type: 0, KeyCode: uinput.Key6},
		"7":     Will{Type: 0, KeyCode: uinput.Key7},
		"8":     Will{Type: 0, KeyCode: uinput.Key8},
		"9":     Will{Type: 0, KeyCode: uinput.Key9},
		"a":     Will{Type: 0, KeyCode: uinput.KeyA},
		"b":     Will{Type: 0, KeyCode: uinput.KeyB},
		"c":     Will{Type: 0, KeyCode: uinput.KeyC},
		"d":     Will{Type: 0, KeyCode: uinput.KeyD},
		"e":     Will{Type: 0, KeyCode: uinput.KeyE},
		"f":     Will{Type: 0, KeyCode: uinput.KeyF},
		"g":     Will{Type: 0, KeyCode: uinput.KeyG},
		"h":     Will{Type: 0, KeyCode: uinput.KeyH},
		"i":     Will{Type: 0, KeyCode: uinput.KeyI},
		"j":     Will{Type: 0, KeyCode: uinput.KeyJ},
		"k":     Will{Type: 0, KeyCode: uinput.KeyK},
		"l":     Will{Type: 0, KeyCode: uinput.KeyL},
		"m":     Will{Type: 0, KeyCode: uinput.KeyM},
		"n":     Will{Type: 0, KeyCode: uinput.KeyN},
		"o":     Will{Type: 0, KeyCode: uinput.KeyO},
		"p":     Will{Type: 0, KeyCode: uinput.KeyP},
		"q":     Will{Type: 0, KeyCode: uinput.KeyQ},
		"r":     Will{Type: 0, KeyCode: uinput.KeyR},
		"s":     Will{Type: 0, KeyCode: uinput.KeyS},
		"t":     Will{Type: 0, KeyCode: uinput.KeyT},
		"u":     Will{Type: 0, KeyCode: uinput.KeyU},
		"v":     Will{Type: 0, KeyCode: uinput.KeyV},
		"w":     Will{Type: 0, KeyCode: uinput.KeyW},
		"x":     Will{Type: 0, KeyCode: uinput.KeyX},
		"y":     Will{Type: 0, KeyCode: uinput.KeyY},
		"z":     Will{Type: 0, KeyCode: uinput.KeyZ},
		".":     Will{Type: 0, KeyCode: uinput.KeyDot},
		"SPACE": Will{Type: 0, KeyCode: uinput.KeySpace},
		"<-":    Will{Type: 0, KeyCode: uinput.KeyBackspace},
		"SHIFT": Will{Type: 1, Action: "shift"},
		"EXIT":  Will{Type: 1, Action: "exit"},
	}

	qwertyOrder := [][]string{
		{"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
		{"q", "w", "e", "r", "t", "y", "u", "i", "o", "p"},
		{"a", "s", "d", "f", "g", "h", "j", "k", "l", "."},
		{"z", "x", "c", "v", "b", "n", "m", "SPACE", "<-", "SHIFT", "quit"},
	}

	// qwertyOrderShift := [][]string{
	// 	{"!", "@", "#", "$", "%", "^", "&", "*", "(", ")"},
	// 	{"q", "w", "e", "r", "t", "y", "u", "i", "o", "p"},
	// 	{"a", "s", "d", "f", "g", "h", "j", "k", "l"},
	// 	{"z", "x", "c", "v", "b", "n", "m", "SPACE", "<-", "SHIFT", "quit"},
	// }

	selectedOrder := qwertyOrder

	shiftIsPressed := false

	var doWill = func(key string) {
		// log.Println("Clicked:", b.Label)
		if v, ok := keyMap[key]; ok {
			if v.Type == 0 {
				keyboard.KeyPress(uint16(v.KeyCode))
			} else if v.Type == 1 {
				if v.Action == "exit" {
					panic(0)
				}
				if v.Action == "shift" {
					if shiftIsPressed {
						keyboard.KeyUp(uinput.KeyLeftShift)
						shiftIsPressed = false
						// selectedOrder
					} else {
						keyboard.KeyDown(uinput.KeyLeftShift)
						shiftIsPressed = true
					}

				}
			}

		}
	}

	const (
		buttonCols  = 10
		buttonWidth = 100
	)

	buttons := []Button{}
	for y, row := range selectedOrder {
		for x, k := range row {
			if _, ok := keyMap[k]; !ok {
				continue
			}
			buttons = append(buttons,
				Button{
					Rect: sdl.Rect{
						X: int32(x * buttonWidth),
						Y: int32(y * buttonWidth),
						W: buttonWidth,
						H: buttonWidth,
					},
					Label: k,
				},
			)

		}
	}

	running := true

	var (
		posX = 0
		posY = 0
	)

	go Pad(func(dir int) {
		if dir == DIR_LEFT {
			posX = max(0, posX-1)
		}
		if dir == DIR_RIGHT {
			posX = min(9, posX+1)
		}
		if dir == DIR_UP {
			posY = max(0, posY-1)
		}
		if dir == DIR_DOWN {
			posY = min(3, posY+1)
		}
		if dir == DIR_X {
			key := qwertyOrder[posY][posX]
			doWill(key)
		}
		fmt.Println(posX, posY)
	})

	for running {
		for event := sdl.PollEvent(); event != nil; event = sdl.PollEvent() {
			switch e := event.(type) {

			case *sdl.QuitEvent:
				running = false

			case *sdl.MouseButtonEvent:
				if e.Type == sdl.MOUSEBUTTONDOWN {
					x, y := e.X, e.Y

					for _, b := range buttons {
						if pointInRect(x, y, b.Rect) {
							doWill(b.Label)
						}

					}
				}
			}
		}

		// Clear background
		renderer.SetDrawColor(30, 30, 30, 255)
		renderer.Clear()

		// Draw buttons with centered text using the helper
		for _, b := range buttons {
			DrawButton(renderer, font, b)
		}

		renderer.SetDrawColor(0, 122, 255, 255)
		renderer.DrawRect(&sdl.Rect{
			X: int32(posX * 100),
			Y: int32(posY * 100),
			W: 100,
			H: 100,
		})

		renderer.Present()
		sdl.Delay(16)
	}
}

func pointInRect(x, y int32, r sdl.Rect) bool {
	return x >= r.X &&
		x <= r.X+r.W &&
		y >= r.Y &&
		y <= r.Y+r.H
}
