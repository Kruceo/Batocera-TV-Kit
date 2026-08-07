package main

import (
	"encoding/binary"
	"log"
	"os"
)

const (
	KEY_UP    = 0x67
	KEY_DOWN  = 0x6c
	KEY_LEFT  = 0x69
	KEY_RIGHT = 0x6a
)

const (
	EV_KEY = 0x01
	EV_ABS = 0x03

	ABS_HAT0X = 0x10
	ABS_HAT0Y = 0x11
	// PlayStation X button (BTN_SOUTH)
	BTN_SOUTH = 0x130
)

type inputEvent struct {
	Time  [16]byte // timeval (ignore)
	Type  uint16
	Code  uint16
	Value int32
}

const DIR_UP = 0
const DIR_DOWN = 1
const DIR_LEFT = 2
const DIR_RIGHT = 3
const DIR_X = 4

func Pad(callback func(dir int)) {
	dev, err := os.Open("/dev/input/event7")
	if err != nil {
		log.Printf("failed to open input device: %v", err)
		return
	}
	defer dev.Close()

	var ev inputEvent

	for {
		err := binary.Read(dev, binary.LittleEndian, &ev)
		if err != nil {
			log.Printf("read error: %v", err)
			return
		}

		if ev.Type == EV_ABS {
			switch ev.Code {

			case ABS_HAT0X:
				if ev.Value == -1 {
					callback(DIR_LEFT)
					println("left")
				} else if ev.Value == 1 {
					callback(DIR_RIGHT)
					println("right")
				}

			case ABS_HAT0Y:
				if ev.Value == -1 {
					callback(DIR_UP)
					println("up")
				} else if ev.Value == 1 {
					callback(DIR_DOWN)
					println("down")
				}
			}
		}
		// Listen for PlayStation X button press
		if ev.Type == EV_KEY && ev.Code == BTN_SOUTH && ev.Value == 1 {
			callback(DIR_X)
			println("X button pressed")
		}
	}
}
