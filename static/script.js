let selectedPosition = {row: null, col: null};

function getCell(row, col) {
    const table = document.getElementById("excelTable");

    if (!table || !table.rows[row + 1] || !table.rows[row + 1].cells[col]) {
        return null;
    }

    return table.rows[row + 1].cells[col];
}

function postCellUpdate(row, col, value) {
    return fetch("/update", {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: `row=${encodeURIComponent(row)}&col=${encodeURIComponent(col)}&value=${encodeURIComponent(value)}`
    });
}

function selectCell(cell) {
    document.querySelectorAll("td").forEach(td => td.classList.remove("selected"));

    cell.classList.add("selected");

    const row = Number(cell.getAttribute("data-row"));
    const col = Number(cell.getAttribute("data-col"));
    selectedPosition = {row, col};

    fetch("/set_position", {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: `row=${row}&col=${col}`
    }).catch(err => {
        alert(`Could not select cell: ${err.message}`);
    });
}

function beginEdit(cell) {
    cell.dataset.editing = "true";
    cell.dataset.originalValue = cell.innerText;
    selectCell(cell);
}

function saveEditedCell(cell) {
    const row = cell.getAttribute("data-row");
    const col = cell.getAttribute("data-col");
    const value = cell.innerText.trim();

    cell.dataset.editing = "false";

    if (cell.dataset.originalValue === value) {
        return;
    }

    postCellUpdate(row, col, value)
        .then(async res => {
            if (!res.ok) {
                throw new Error(await res.text());
            }
        })
        .catch(err => {
            alert(`Cell update failed: ${err.message}`);
            cell.innerText = cell.dataset.originalValue || "";
        });
}

function handleCellKeydown(event, cell) {
    if (event.key === "Enter") {
        event.preventDefault();
        cell.blur();
    }
}

function syncSelectedCell() {
    fetch("/get_position")
        .then(res => res.json())
        .then(pos => {
            if (pos.row === null || pos.col === null || pos.row === undefined || pos.col === undefined) {
                selectedPosition = {row: null, col: null};
                document.querySelectorAll("td").forEach(td => td.classList.remove("selected"));
                return;
            }

            selectedPosition = {
                row: Number(pos.row),
                col: Number(pos.col)
            };
            const cell = getCell(Number(pos.row), Number(pos.col));

            if (cell) {
                document.querySelectorAll("td").forEach(td => td.classList.remove("selected"));
                cell.classList.add("selected");
            }
        });
}

function syncVoiceStatus() {
    fetch("/voice_status")
        .then(res => res.json())
        .then(status => {
            const stateEl = document.getElementById("voiceState");
            const messageEl = document.getElementById("voiceMessage");
            const textEl = document.getElementById("voiceText");
            const cellEl = document.getElementById("voiceCell");

            if (!stateEl || !messageEl || !textEl || !cellEl) {
                return;
            }

            stateEl.innerText = status.state || "idle";
            messageEl.innerText = status.message || "-";
            textEl.innerText = status.text || "-";

            if (status.row === null || status.row === undefined || status.col === null || status.col === undefined) {
                cellEl.innerText = "-";
            } else {
                cellEl.innerText = `row ${Number(status.row) + 1}, col ${Number(status.col) + 1}`;
            }

            if (status.state === "success" && status.row !== null && status.col !== null && status.text) {
                const targetCell = getCell(Number(status.row), Number(status.col));

                if (targetCell && targetCell.dataset.editing !== "true") {
                    targetCell.innerText = status.text;
                }
            }
        })
        .catch(() => {});
}

// refresh UI
setInterval(() => {
    fetch("/get_data")
        .then(res => res.json())
        .then(data => {
            const table = document.getElementById("excelTable");
            if (!table) {
                return;
            }
            const cols = Object.keys(data);

            for (let j = 0; j < cols.length; j++) {
                const col = cols[j];

                for (let i = 0; i < data[col].length; i++) {
                    const cell = table.rows[i + 1]?.cells[j];

                    if (cell && cell.dataset.editing !== "true") {
                        const value = data[col][i] ?? "";
                        cell.innerText = value;
                    }
                }
            }
        })
        .catch(() => {});
}, 500);

setInterval(syncSelectedCell, 500);
setInterval(syncVoiceStatus, 500);
syncVoiceStatus();

// voice control
function startVoice() {
    if (selectedPosition.row === null || selectedPosition.col === null) {
        alert("Select a cell first.");
        return;
    }

    const body = `row=${encodeURIComponent(selectedPosition.row)}&col=${encodeURIComponent(selectedPosition.col)}`;

    fetch("/start_voice", {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body
    })
        .then(async res => {
            const message = await res.text();
            if (!res.ok) {
                throw new Error(message);
            }
            alert(message);
        })
        .catch(err => alert(err.message));
}

function stopVoice() {
    fetch("/stop_voice")
        .then(async res => {
            const message = await res.text();
            if (!res.ok) {
                throw new Error(message);
            }
            alert(message);
        })
        .catch(err => alert(err.message));
}

// download
function downloadExcel() {
    window.location.href = "/download_excel";
}

function downloadCSV() {
    window.location.href = "/download_csv";
}
