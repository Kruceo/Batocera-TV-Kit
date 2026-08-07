function simulateEsc() {
    const eventOptions = {
        key: "Escape",
        code: "Escape",
        keyCode: 27,
        which: 27,
        bubbles: true,
        cancelable: true
    };

    // 1️⃣ Eventos de teclado
    const keydown = new KeyboardEvent("keydown", eventOptions);
    const keypress = new KeyboardEvent("keypress", eventOptions);
    const keyup = new KeyboardEvent("keyup", eventOptions);

    window.dispatchEvent(keydown);
    window.dispatchEvent(keypress);
    window.dispatchEvent(keyup);
    document.dispatchEvent(keydown);
    document.dispatchEvent(keypress);
    document.dispatchEvent(keyup);

    // 2️⃣ Eventos de input / antes do input
    const inputEvent = new InputEvent("input", { bubbles: true, cancelable: true });
    const beforeInputEvent = new InputEvent("beforeinput", { bubbles: true, cancelable: true });
    const changeEvent = new Event("change", { bubbles: true, cancelable: true });

    // dispara nos elementos focados
    const activeEl = document.activeElement;
    if (activeEl) {
        activeEl.dispatchEvent(inputEvent);
        activeEl.dispatchEvent(beforeInputEvent);
        activeEl.dispatchEvent(changeEvent);
    }

    // 3️⃣ Evento genérico
    const genericEvent = new Event("keydown", { bubbles: true, cancelable: true });
    window.dispatchEvent(genericEvent);
    document.dispatchEvent(genericEvent);

    console.log("Simulated ESC events dispatched");
}

// Exemplo de uso


window.addEventListener("keydown", function (e) {
    if (e.shiftKey && e.code === "Backspace") {
        e.preventDefault();
        e.stopImmediatePropagation();

        simulateEsc();
        alert(1)
    }
}, { capture: true });
