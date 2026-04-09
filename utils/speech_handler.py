import speech_recognition as sr
import requests
import time


SERVER = "http://127.0.0.1:5000"
#SERVER = "https://voice-excel-update-npvj-fcybtqjx7-rajukushwaha-svgs-projects.vercel.app/""

running = False


def get_current_position():
    response = requests.get(SERVER + "/get_position", timeout=5)
    response.raise_for_status()
    pos = response.json()

    row = pos.get("row")
    col = pos.get("col")

    if row is None or col is None:
        return None, None

    return int(row), int(col)


def get_active_voice_position():
    response = requests.get(SERVER + "/get_active_voice_position", timeout=5)
    response.raise_for_status()
    pos = response.json()

    row = pos.get("row")
    col = pos.get("col")

    if row is None or col is None:
        return None, None

    return int(row), int(col)


def send_status(state, message, text="", row=None, col=None):
    try:
        requests.post(
            SERVER + "/voice_status",
            json={
                "state": state,
                "message": message,
                "text": text,
                "row": row,
                "col": col
            },
            timeout=5
        )
    except requests.RequestException:
        pass


def start_voice():
    global running

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold = 0.5
    r.dynamic_energy_threshold = True

    mic = sr.Microphone()

    print("🎤 Voice Started")
    print("Select a cell, then speak...")
    try:
        row, col = get_active_voice_position()
    except requests.RequestException:
        row, col = None, None

    if row is None or col is None:
        send_status("error", "Select a cell before starting voice.")
        running = False
        return

    send_status("listening", "Listening for speech...", row=row, col=col)

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)

        while running:
            try:
                locked_row, locked_col = get_active_voice_position()
                if locked_row is None or locked_col is None:
                    send_status("error", "Select a cell before speaking.")
                    time.sleep(0.2)
                    continue

                row, col = locked_row, locked_col
                send_status("listening", "Listening for speech...", row=row, col=col)
                audio = r.listen(source, timeout=5, phrase_time_limit=5)

                text = r.recognize_google(audio, language="en-IN")
                print("You said:", text)
                locked_row, locked_col = get_active_voice_position()
                if locked_row is None or locked_col is None:
                    send_status("error", "Voice target cell is no longer active.", text=text)
                    continue
                row, col = locked_row, locked_col
                send_status("recognized", "Speech recognized.", text=text, row=row, col=col)

                print("Fill:", row, col)
                send_status("updating", f"Updating row {row + 1}, column {col + 1}.", text=text, row=row, col=col)

                update_response = requests.post(SERVER + "/update", data={
                    "row": row,
                    "col": col,
                    "value": text
                }, timeout=5)
                update_response.raise_for_status()
                send_status(
                    "success",
                    f"Updated selected cell at row {row + 1}, column {col + 1}.",
                    text=text,
                    row=row,
                    col=col
                )

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("Could not understand audio. Please speak again.")
                send_status("error", "Could not understand audio. Please speak again.")
                time.sleep(0.2)
            except requests.RequestException as e:
                print("Server error:", e)
                send_status("error", f"Server error: {e}")
                time.sleep(0.5)
            except Exception as e:
                print("Voice error:", e)
                send_status("error", f"Voice error: {e}")
                time.sleep(0.5)
