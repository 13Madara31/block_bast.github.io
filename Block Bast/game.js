// Получаем элементы из HTML
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const blocks = [document.getElementById('block1'), document.getElementById('block2'), document.getElementById('block3')];
const restartBtn = document.getElementById('restart-btn');
const draggableBlocksWrapper = document.querySelector('.draggable-blocks-wrapper');

// Элементы модального окна настроек
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsModalBtn = settingsModal.querySelector('.btn-close-settings-modal');
const musicToggle = document.getElementById('musicToggle');
const soundToggle = document.getElementById('soundToggle');
const restartGameFromSettingsBtn = document.getElementById('restart-game-from-settings');

// Получаем выбранную роль из localStorage
const selectedRole = localStorage.getItem('selectedCharacterRole') || 'архимаг'; // По умолчанию - Архимаг

// Цветовые схемы для ролей (соответствуют CSS-переменным)
const roleColors = {
    'архимаг': {
        gridFill: '#FFEB3B', // Яркий Желтый
        gridStroke: '#FDD835', // Более темный Желтый для рамки сетки
        ghostFill: 'rgba(255, 235, 59, 0.7)', // Яркий Желтый полупрозрачный
        ghostError: 'rgba(255, 0, 0, 0.8)', // Красный полупрозрачный
        blockBackground: '#FFEB3B', // Яркий Желтый для фона блока
        blockBorder: '#FDD835' // Более темный Желтый для границы блока
    },
    'провидец': {
        gridFill: '#00FFFF', // Яркий Циан
        gridStroke: '#00E6E6', // Более темный Циан
        ghostFill: 'rgba(0, 255, 255, 0.7)', // Яркий Циан полупрозрачный
        ghostError: 'rgba(255, 0, 0, 0.8)', // Красный полупрозрачный
        blockBackground: '#00FFFF',
        blockBorder: '#00E6E6'
    },
    'инженер': {
        gridFill: '#7CFC00', // Яркий Салатовый
        gridStroke: '#ADFF2F', // Яркий Зелено-желтый
        ghostFill: 'rgba(124, 252, 0, 0.7)', // Яркий Салатовый полупрозрачный
        ghostError: 'rgba(255, 0, 0, 0.8)', // Красный полупрозрачный
        blockBackground: '#7CFC00',
        blockBorder: '#ADFF2F'
    },
    'монархтеней': {
        gridFill: '#8A2BE2', // Сине-фиолетовый
        gridStroke: '#9370DB', // Средний сиреневый
        ghostFill: 'rgba(138, 43, 226, 0.7)', // Сине-фиолетовый полупрозрачный
        ghostError: 'rgba(255, 0, 0, 0.8)', // Красный полупрозрачный
        blockBackground: '#8A2BE2',
        blockBorder: '#9370DB'
    }
};

const currentRoleColors = roleColors[selectedRole];

// Константы
const GRID_SIZE = 8;
let CELL_SIZE; // Теперь CELL_SIZE будет динамическим

// Функция для установки CELL_SIZE и размеров канваса
function setCanvasSize() {
    // Получаем текущую вычислимую ширину canvas из CSS
    const canvasComputedWidth = parseFloat(getComputedStyle(canvas).width);
    // Вычисляем CELL_SIZE так, чтобы он был целым числом и канвас был ровно заполнен
    CELL_SIZE = Math.floor(canvasComputedWidth / GRID_SIZE);
    
    // Устанавливаем размеры canvas, чтобы они были кратны CELL_SIZE
    canvas.width = GRID_SIZE * CELL_SIZE;
    canvas.height = GRID_SIZE * CELL_SIZE;
}

// Переменные игры
let grid = Array(GRID_SIZE).fill().map(() => Array(GRID_SIZE).fill(0));
let score = 0;
let currentBlocks = [];
let ghostShape = null;
let ghostX = 0, ghostY = 0;

// Переменные для touch-событий
let activeTouch = null;
let draggedBlock = null;
let isDragging = false;

// Формы блоков
const shapes = [
    // [[1, 1]], // Удален блок 1x1
    // [[1], [1]],
    [[1, 1], [1, 1]], // O-Shape
    [[1, 1, 1, 1]], // I-Shape (horizontal)
    [[1], [1], [1], [1]], // I-Shape (vertical)
    [[0, 1, 0], [1, 1, 1]], // T-Shape
    [[1, 1, 0], [0, 1, 1]], // S-Shape
    [[0, 1, 1], [1, 1, 0]], // Z-Shape
    [[1, 0, 0], [1, 1, 1]], // J-Shape
    [[0, 0, 1], [1, 1, 1]] // L-Shape
];

// Функции для управления звуком и музыкой
let isMusicOn = localStorage.getItem('isMusicOn') === 'true';
let isSoundOn = localStorage.getItem('isSoundOn') === 'true';

function updateMusicToggle() {
    musicToggle.checked = isMusicOn;
    // Здесь можно добавить логику для включения/выключения фоновой музыки
}

function updateSoundToggle() {
    soundToggle.checked = isSoundOn;
    // Здесь можно добавить логику для включения/выключения звуковых эффектов
}

// Генерация умных блоков
function generateSmartBlocks() {
    currentBlocks = [];
    for (let i = 0; i < 3; i++) {
        let shape;
        let attempts = 0;
        do {
            shape = shapes[Math.floor(Math.random() * shapes.length)];
            attempts++;
        } while (!canPlaceAny(shape) && attempts < 10);
        currentBlocks.push(shape);
        setTimeout(() => updateBlockUI(i, shape), i * 400);
    }
}

// Проверка возможности размещения формы где-либо на поле
function canPlaceAny(shape) {
    for (let y = 0; y <= GRID_SIZE - shape.length; y++) {
        for (let x = 0; x <= GRID_SIZE - shape[0].length; x++) {
            if (canPlace(shape, x, y)) return true;
        }
    }
    return false;
}

// Проверка, что ни один из текущих блоков не может быть размещен
function isGameOver() {
    return currentBlocks.every(shape => !canPlaceAny(shape));
}

// Проверка размещения формы в конкретной позиции
function canPlace(shape, startX, startY) {
    for (let y = 0; y < shape.length; y++) {
        for (let x = 0; x < shape[y].length; x++) {
            if (shape[y][x] && (grid[startY + y][startX + x] !== 0)) return false;
        }
    }
    return true;
}

// Размещение формы на поле
function placeShape(shape, startX, startY) {
    for (let y = 0; y < shape.length; y++) {
        for (let x = 0; x < shape[y].length; x++) {
            if (shape[y][x]) grid[startY + y][startX + x] = 1;
        }
    }
    // Передаем колбэк в checkLines, который будет вызван после очистки линий
    checkLines(() => {
        const index = currentBlocks.indexOf(shape);
        if (index > -1) currentBlocks.splice(index, 1);
        
        // После размещения блока, всегда обновляем UI и затем проверяем условия
        blocks.forEach((block, i) => {
            if (i < currentBlocks.length) {
                updateBlockUI(i, currentBlocks[i]);
            } else {
                block.innerHTML = '';
            }
        });

        if (currentBlocks.length === 0) {
            generateSmartBlocks(); // Всегда генерируем новые блоки, если текущий набор исчерпан
        }
        
        // Проверяем Game Over после всех обновлений
        if (isGameOver()) {
            handleGameOver();
        }
    });
}

// Обработка конца игры
function handleGameOver() {
    const playerName = 'Игрок'; // Имя игрока по умолчанию
    saveGameScore(playerName, score);
    alert(`Игра окончена! Ваш финальный счет: ${score}. Рекорд сохранен под именем ${playerName}.`);
    // При окончании игры скрываем draggable-blocks-wrapper и показываем restart-btn
    draggableBlocksWrapper.classList.add('hidden');
    restartBtn.classList.remove('hidden');
}

// Функция сохранения игрового счета в рейтинг
function saveGameScore(name, gameScore) {
    const ranking = JSON.parse(localStorage.getItem('blockBlastRanking') || '[]');
    
    ranking.push({
        name: name,
        score: gameScore,
        date: new Date().toLocaleDateString('ru-RU')
    });
    
    ranking.sort((a, b) => b.score - a.score);
    
    // Оставляем только топ-10
    const top10 = ranking.slice(0, 10);
    
    localStorage.setItem('blockBlastRanking', JSON.stringify(top10));

    // Обновляем общий рекорд, если текущий счет выше
    let currentHighScore = parseInt(localStorage.getItem('blockBlastHighScore'), 10) || 0;
    if (gameScore > currentHighScore) {
        localStorage.setItem('blockBlastHighScore', gameScore);
        
        // Отправляем новый рекорд на сервер Telegram бота
        sendHighScoreToServer(name, selectedRole, gameScore);
    }
}

// Функция для отправки данных о новом рекорде на сервер Flask
function sendHighScoreToServer(username, role, score) {
    const serverUrl = 'https://block-blast-telegram-bot.onrender.com/new_high_score'; // Адрес вашего Flask сервера
    fetch(serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, role, score }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Рекорд отправлен на сервер', data);
    })
    .catch((error) => {
        console.error('Ошибка при отправке рекорда на сервер:', error);
    });
}

// Проверка и очистка линий
function checkLines(callback) {
    let linesCleared = 0;
    const rowsToClear = [];
    const colsToClear = [];

    // Определяем горизонтальные линии для очистки
    for (let y = 0; y < GRID_SIZE; y++) {
        if (grid[y].every(cell => cell !== 0)) {
            rowsToClear.push(y);
        }
    }

    // Определяем вертикальные линии для очистки
    for (let x = 0; x < GRID_SIZE; x++) {
        if (grid.every(row => row[x] !== 0)) {
            colsToClear.push(x);
        }
    }

    if (rowsToClear.length > 0 || colsToClear.length > 0) {
        // Запускаем анимацию взрыва для всех найденных линий
        rowsToClear.forEach(y => explodeLine(y, 'horizontal'));
        colsToClear.forEach(x => explodeLine(x, 'vertical'));

        // Немедленно очищаем линии из сетки и обновляем счет
        setTimeout(() => {
            rowsToClear.forEach(y => {
                grid[y] = Array(GRID_SIZE).fill(0);
                linesCleared++;
            });
            colsToClear.forEach(x => {
                for (let y = 0; y < GRID_SIZE; y++) grid[y][x] = 0;
                linesCleared++;
            });
            
            score += linesCleared * 100;
            scoreEl.textContent = score;
            draw(); // Перерисовываем поле после очистки и обновления счета
            if (callback) callback(); // Вызываем колбэк после завершения очистки и обновления
        }, 500); // Небольшая задержка, чтобы анимация взрыва успела начаться
    } else {
        draw(); // Перерисовываем поле, чтобы показать размещенный блок, если линий нет
        if (callback) callback(); // Вызываем колбэк сразу, если линий не было
    }
}

// Взрыв линии с частицами
function explodeLine(index, type) {
    const colors = [
        currentRoleColors.gridFill, 
        currentRoleColors.blockBackground, 
        currentRoleColors.ghostFill.replace('0.7', '1'), // Более насыщенный цвет
        '#ffffff' // Добавим немного белого для контраста
    ];
    const gameContainer = document.querySelector('.game_container');
    
    for (let i = 0; i < 40; i++) { // Уменьшено количество частиц для оптимизации
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const centerX = type === 'horizontal' ? Math.random() * (GRID_SIZE * CELL_SIZE) : index * CELL_SIZE + CELL_SIZE / 2;
        const centerY = type === 'horizontal' ? index * CELL_SIZE + CELL_SIZE / 2 : Math.random() * (GRID_SIZE * CELL_SIZE);
        
        particle.style.left = `${centerX}px`;
        particle.style.top = `${centerY}px`;
        particle.style.width = `${Math.random() * 12 + 8}px`; // Разнообразные размеры частиц
        particle.style.height = particle.style.width;
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        
        let tx, ty;
        const spreadFactor = 1.5; // Коэффициент разлета частиц за пределы поля (1.5 = 150% от размера поля)

        if (type === 'horizontal') {
            tx = (Math.random() - 0.5) * (GRID_SIZE * CELL_SIZE * spreadFactor); // Разлет вдоль линии
            ty = (Math.random() - 0.5) * (GRID_SIZE * CELL_SIZE * spreadFactor); // Разлет перпендикулярно линии, чтобы доходило до краев поля
        } else { // vertical
            tx = (Math.random() - 0.5) * (GRID_SIZE * CELL_SIZE * spreadFactor); // Разлет перпендикулярно линии, чтобы доходило до краев поля
            ty = (Math.random() - 0.5) * (GRID_SIZE * CELL_SIZE * spreadFactor); // Разлет вдоль линии
        }
        particle.style.setProperty('--tx', `${tx}px`);
        particle.style.setProperty('--ty', `${ty}px`);
        
        gameContainer.appendChild(particle);
        setTimeout(() => particle.remove(), 1200);
    }
}

// Рисование поля и блоков
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Рисуем сетку и занятые клетки
    for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
            if (grid[y][x]) {
                const rectX = x * CELL_SIZE;
                const rectY = y * CELL_SIZE;
                const rectSize = CELL_SIZE;
                const cornerRadius = 8; // Радиус закругления

                // Используем цвет фона блока для заливки
                ctx.fillStyle = currentRoleColors.blockBackground;
                // Используем цвет границы блока для обводки
                ctx.strokeStyle = currentRoleColors.blockBorder;
                ctx.lineWidth = 4; // Толщина рамки, как у перетаскиваемых блоков

                // Рисуем закругленный прямоугольник
                ctx.beginPath();
                ctx.moveTo(rectX + cornerRadius, rectY);
                ctx.lineTo(rectX + rectSize - cornerRadius, rectY);
                ctx.quadraticCurveTo(rectX + rectSize, rectY, rectX + rectSize, rectY + cornerRadius);
                ctx.lineTo(rectX + rectSize, rectY + rectSize - cornerRadius);
                ctx.quadraticCurveTo(rectX + rectSize, rectY + rectSize, rectX + rectSize - cornerRadius, rectY + rectSize);
                ctx.lineTo(rectX + cornerRadius, rectY + rectSize);
                ctx.quadraticCurveTo(rectX, rectY + rectSize, rectX, rectY + rectSize - cornerRadius);
                ctx.lineTo(rectX, rectY + cornerRadius);
                ctx.quadraticCurveTo(rectX, rectY, rectX + cornerRadius, rectY);
                ctx.closePath();
                ctx.fill();   // Заливаем
                ctx.stroke(); // Обводим

                // Добавляем тень для объема, используя цвет фона блока
                ctx.shadowColor = currentRoleColors.blockBackground;
                ctx.shadowBlur = 5; // Уменьшено размытие тени для оптимизации
                ctx.shadowOffsetX = 2;
                ctx.shadowOffsetY = 2;
            } else {
                ctx.shadowBlur = 0;
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;
                // Для пустых клеток рисуем только сетку, без заливки
                ctx.strokeStyle = currentRoleColors.gridStroke;
                ctx.lineWidth = 1; // Возвращаем стандартную толщину линии для сетки
                ctx.strokeRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            }
        }
    }
    // Сбрасываем тени и стили для следующих элементов (призраков)
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    ctx.lineWidth = 1; // Сброс толщины линии для общего рисования

    // Рисуем превью размещения
    if (ghostShape) {
        for (let y = 0; y < ghostShape.length; y++) {
            for (let x = 0; x < ghostShape[y].length; x++) {
                if (ghostShape[y][x]) {
                    const ghostRectX = (ghostX + x) * CELL_SIZE;
                    const ghostRectY = (ghostY + y) * CELL_SIZE;
                    const ghostRectSize = CELL_SIZE;
                    const ghostCornerRadius = 8; // Радиус закругления для призрака

                    // Используем цвета призрака для заливки
                    ctx.fillStyle = canPlace(ghostShape, ghostX, ghostY) ? currentRoleColors.ghostFill : currentRoleColors.ghostError;
                    // Используем цвет границы блока для обводки
                    ctx.strokeStyle = currentRoleColors.blockBorder;
                    ctx.lineWidth = 4; // Толщина рамки

                    // Рисуем закругленный прямоугольник для призрака
                    ctx.beginPath();
                    ctx.moveTo(ghostRectX + ghostCornerRadius, ghostRectY);
                    ctx.lineTo(ghostRectX + ghostRectSize - ghostCornerRadius, ghostRectY);
                    ctx.quadraticCurveTo(ghostRectX + ghostRectSize, ghostRectY, ghostRectX + ghostRectSize, ghostRectY + ghostCornerRadius);
                    ctx.lineTo(ghostRectX + ghostRectSize, ghostRectY + ghostRectSize - ghostCornerRadius);
                    ctx.quadraticCurveTo(ghostRectX + ghostRectSize, ghostRectY + ghostRectSize, ghostRectX + ghostRectSize - ghostCornerRadius, ghostRectY + ghostRectSize);
                    ctx.lineTo(ghostRectX + ghostCornerRadius, ghostRectY + ghostRectSize);
                    ctx.quadraticCurveTo(ghostRectX, ghostRectY + ghostRectSize, ghostRectX, ghostRectY + ghostRectSize - ghostCornerRadius);
                    ctx.lineTo(ghostRectX, ghostRectY + ghostCornerRadius);
                    ctx.quadraticCurveTo(ghostRectX, ghostRectY, ghostRectX + ghostCornerRadius, ghostRectY);
                    ctx.closePath();
                    ctx.fill();   // Заливаем
                    ctx.stroke(); // Обводим

                    // Добавляем тень для объема призрака
                    ctx.shadowColor = canPlace(ghostShape, ghostX, ghostY) ? currentRoleColors.ghostFill : currentRoleColors.ghostError;
                    ctx.shadowBlur = 5; // Уменьшено размытие тени для оптимизации
                    ctx.shadowOffsetX = 2;
                    ctx.shadowOffsetY = 2;
                }
            }
        }
    }
    // Сбрасываем тени после отрисовки призрака
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    ctx.lineWidth = 1; // Сброс толщины линии для общего рисования
}

// Обновление UI блоков
function updateBlockUI(index, shape) {
    const blockEl = blocks[index];
    blockEl.innerHTML = '';
    
    const cols = shape[0].length;
    const rows = shape.length;
    const cellSize = CELL_SIZE; // Используем глобальный CELL_SIZE
    
    // Устанавливаем размеры блока, чтобы он мог центрировать внутренние ячейки
    blockEl.style.width = `${cols * cellSize}px`;
    blockEl.style.height = `${rows * cellSize}px`;
    
    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            if (shape[y][x]) {
                const cell = document.createElement('div');
                cell.style.position = 'absolute'; // Оставляем absolute для точного позиционирования внутри flex-контейнера blockEl
                cell.style.left = `${x * cellSize}px`;
                cell.style.top = `${y * cellSize}px`;
                cell.style.width = `${cellSize}px`;
                cell.style.height = `${cellSize}px`;
                cell.style.backgroundColor = currentRoleColors.blockBackground;
                cell.style.border = `4px solid ${currentRoleColors.blockBorder}`;
                cell.style.borderRadius = '10px';
                cell.style.transition = 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                blockEl.appendChild(cell);
            }
        }
    }
}

// Функции для обработки touch-событий
function getTouchPos(touch) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: Math.floor((touch.clientX - rect.left) / CELL_SIZE),
        y: Math.floor((touch.clientY - rect.top) / CELL_SIZE)
    };
}

function startDrag(index, touch) {
    if (index < currentBlocks.length) {
        draggedBlock = index;
        isDragging = true;
        activeTouch = touch.identifier;
        
        const block = blocks[index];
        block.classList.add('dragging');
        
        ghostShape = currentBlocks[index];
        updateGhostPosition(touch);
        draw();
    }
}

function updateGhostPosition(touch) {
    const pos = getTouchPos(touch);
    
    // Корректируем координаты, чтобы верхний левый угол блока соответствовал курсору
    // и блок оставался в пределах сетки
    ghostX = Math.max(0, Math.min(pos.x, GRID_SIZE - ghostShape[0].length));
    ghostY = Math.max(0, Math.min(pos.y, GRID_SIZE - ghostShape.length));
    draw(); // Перерисовываем призрак при каждом движении
}

function endDrag(touch) {
    if (isDragging && draggedBlock !== null && draggedBlock < currentBlocks.length) {
        const pos = getTouchPos(touch);
        const x = Math.max(0, Math.min(pos.x, GRID_SIZE - currentBlocks[draggedBlock][0].length));
        const y = Math.max(0, Math.min(pos.y, GRID_SIZE - currentBlocks[draggedBlock].length));
        
        if (canPlace(currentBlocks[draggedBlock], x, y)) {
            placeShape(currentBlocks[draggedBlock], x, y);
        }
        
        resetDrag();
    }
}

function resetDrag() {
    if (draggedBlock !== null) {
        blocks[draggedBlock].classList.remove('dragging');
    }
    draggedBlock = null;
    isDragging = false;
    activeTouch = null;
    ghostShape = null;
    draw();
}

// Drag-and-drop для десктопа
blocks.forEach((block, index) => {
    // Десктоп события
    block.addEventListener('dragstart', (e) => {
        draggedBlock = index;
        block.classList.add('dragging');
    });
    
    block.addEventListener('dragend', () => {
        resetDrag();
    });

    // Touch события
    block.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (e.touches.length === 1) {
            startDrag(index, e.touches[0]);
        }
    }, { passive: false });

    block.addEventListener('touchmove', (e) => {
        e.preventDefault();
        if (isDragging && activeTouch !== null) {
            const touch = Array.from(e.touches).find(t => t.identifier === activeTouch);
            if (touch) {
                updateGhostPosition(touch);
                draw();
            }
        }
    }, { passive: false });

    block.addEventListener('touchend', (e) => {
        e.preventDefault();
        if (isDragging && activeTouch !== null) {
            const touch = Array.from(e.changedTouches).find(t => t.identifier === activeTouch);
            if (touch) {
                endDrag(touch);
            }
        }
    }, { passive: false });

    block.addEventListener('touchcancel', (e) => {
        e.preventDefault();
        resetDrag();
    }, { passive: false });
});

// Обработчики для canvas
canvas.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (draggedBlock !== null && draggedBlock < currentBlocks.length) {
        const rect = canvas.getBoundingClientRect();
        let newGhostX = Math.floor((e.clientX - rect.left) / CELL_SIZE);
        let newGhostY = Math.floor((e.clientY - rect.top) / CELL_SIZE);
        ghostShape = currentBlocks[draggedBlock];

        // Ограничиваем ghostX и ghostY, чтобы фигура не выходила за границы поля
        ghostX = Math.max(0, Math.min(newGhostX, GRID_SIZE - ghostShape[0].length));
        ghostY = Math.max(0, Math.min(newGhostY, GRID_SIZE - ghostShape.length));
        
        draw();
    }
});

canvas.addEventListener('drop', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / CELL_SIZE);
    const y = Math.floor((e.clientY - rect.top) / CELL_SIZE);
    if (draggedBlock !== null && draggedBlock < currentBlocks.length && canPlace(currentBlocks[draggedBlock], x, y)) {
        placeShape(currentBlocks[draggedBlock], x, y);
        resetDrag();
    }
});

// Touch события для canvas
canvas.addEventListener('touchmove', (e) => {
    if (isDragging && activeTouch !== null) {
        e.preventDefault();
        const touch = Array.from(e.touches).find(t => t.identifier === activeTouch);
        if (touch) {
            updateGhostPosition(touch);
            draw();
        }
    }
}, { passive: false });

canvas.addEventListener('touchend', (e) => {
    if (isDragging && activeTouch !== null) {
        e.preventDefault();
        const touch = Array.from(e.changedTouches).find(t => t.identifier === activeTouch);
        if (touch) {
            endDrag(touch);
        }
    }
}, { passive: false });

// --- Функционал кнопок и модального окна настроек ---
settingsBtn.addEventListener('click', () => {
    settingsModal.classList.add('active');
    updateMusicToggle(); // Обновляем состояние переключателей
    updateSoundToggle();
});

closeSettingsModalBtn.addEventListener('click', () => {
    settingsModal.classList.remove('active');
});

musicToggle.addEventListener('change', (e) => {
    isMusicOn = e.target.checked;
    localStorage.setItem('isMusicOn', isMusicOn);
    // Дополнительная логика для музыки
});

soundToggle.addEventListener('change', (e) => {
    isSoundOn = e.target.checked;
    localStorage.setItem('isSoundOn', isSoundOn);
    // Дополнительная логика для звуков
});

restartGameFromSettingsBtn.addEventListener('click', () => {
    resetGame(); // Функция для полного перезапуска игры
    settingsModal.classList.remove('active'); // Закрываем модальное окно
});

// Рестарт игры (основная кнопка)
restartBtn.addEventListener('click', () => {
    resetGame();
});

// Обработчик для кнопки рестарт на touch устройствах (основная кнопка)
restartBtn.addEventListener('touchend', (e) => {
    e.preventDefault();
    resetGame();
});

function resetGame() {
    grid = Array(GRID_SIZE).fill().map(() => Array(GRID_SIZE).fill(0));
    score = 0;
    scoreEl.textContent = score;
    generateSmartBlocks();
    draw();
    draggableBlocksWrapper.classList.remove('hidden'); // Показываем блоки
    restartBtn.classList.add('hidden'); // Скрываем основную кнопку рестарта
}

// Предотвращаем масштабирование при двойном тапе
blocks.forEach(block => {
    block.addEventListener('touchend', (e) => {
        if (e.touches.length === 0) {
            e.preventDefault();
        }
    }, { passive: false });
});

// Инициализация игры
setCanvasSize(); // Устанавливаем размер канваса при старте
generateSmartBlocks();
draw();

// Обработка изменения размера окна
window.addEventListener('resize', () => {
    setCanvasSize(); // Пересчитываем размер канваса при изменении размера окна
    draw();
});