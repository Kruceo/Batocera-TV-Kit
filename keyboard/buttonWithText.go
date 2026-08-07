package main

import (
	"log"

	"github.com/veandco/go-sdl2/sdl"
	"github.com/veandco/go-sdl2/ttf"
)

// Button represents a clickable button with a label
type Button struct {
	Rect  sdl.Rect
	Label string
}

// DrawButton draws a button with its background, border and centered text
func DrawButton(renderer *sdl.Renderer, font *ttf.Font, button Button) {
	// Draw button background
	renderer.SetDrawColor(70, 70, 70, 255)
	renderer.FillRect(&button.Rect)

	// Draw button border
	renderer.SetDrawColor(120, 120, 120, 255)
	renderer.DrawRect(&button.Rect)

	// Draw centered text
	DrawCenteredText(renderer, font, button.Label, button.Rect)
}

// DrawCenteredText renders text centered within a rectangle
func DrawCenteredText(renderer *sdl.Renderer, font *ttf.Font, text string, rect sdl.Rect) {
	// Render text to surface
	color := sdl.Color{R: 255, G: 255, B: 255, A: 255}
	surface, err := font.RenderUTF8Solid(text, color)
	if err != nil {
		log.Println("Error rendering text:", err)
		return
	}
	defer surface.Free()

	// Create texture from surface
	texture, err := renderer.CreateTextureFromSurface(surface)
	if err != nil {
		log.Println("Error creating texture:", err)
		return
	}
	defer texture.Destroy()

	// Calculate centered position
	textWidth := surface.W
	textHeight := surface.H

	dstRect := sdl.Rect{
		X: rect.X + (rect.W-textWidth)/2,
		Y: rect.Y + (rect.H-textHeight)/2,
		W: textWidth,
		H: textHeight,
	}

	// Copy texture to renderer
	renderer.Copy(texture, nil, &dstRect)
}
