// static/game.js
// MVP: word_flash + nicer UI + OGG voice lines (no TTS)
// Expects HTML ids: btnSound, pillStatus, sessionInfo, speedInfo, progressBar, timerRing,
// word, options, toast, btnPlay, btnRestart, childName, childSelect, resultBlock, stars,
// kpiAcc, kpiReact, kpiNext

let session = null;
let items = [];
let idx = 0;

let gameMode = "word_flash";
let livesStart = 0;
let livesLeft = 0;

// survival stats
let survStartedAtMs = 0;
let survCorrect = 0;
let survWrong = 0;
let survStreak = 0;
let survBestStreak = 0;
let survDead = false; // умер по жизням

let shownAt = 0;
let hideTimer = null;
let ringTimer = null;
let lbTyped = "";
let lbLocked = false;

function lbReset() {
  lbTyped = "";
  lbLocked = false;
}

function choosePromptForMode(mode) {
  if (mode === "letter_builder") return "";
  if (mode === "odd_one_out") return "Выбери лишнее слово:";
  if (mode === "vocab_spell") return "Вставь пропущенную букву:";
  return "Выбери правильный вариант:";
}

async function loadThemes(){
  const sel = document.getElementById("themeSelect");
  if (!sel) return;

  const themes = await api("/api/themes");
  sel.innerHTML = "";

  themes.forEach(t => {
    const opt = document.createElement("option");
    opt.textContent = t.name;   // показываем только название
    opt.value = String(t.id);   // id остаётся в value
    sel.appendChild(opt);
  });

  // дефолт
const saved = localStorage.getItem("rg_theme_id");
  if (saved) sel.value = saved;

  sel.dispatchEvent(new Event("change", { bubbles: true }));

  if (typeof window.filterThemesByMode === "function") {
    window.filterThemesByMode(window.rg_selected_mode || "word_flash");
  }
}

// ===================== API =====================
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
function $(id) { return document.getElementById(id); }

// ===================== AUDIO (OGG) =====================
// Notes:
// - Put files under: static/audio/<type>/<file>.ogg
// - For "living" voice: record multiple short variants in each category.
// - We avoid interrupting a currently playing voice line by default.

let soundOn = true;

// "soft" = подсказки только иногда
// "full" = подсказки всегда
let voiceMode = "full";

const audioCache = {};      // key -> Audio
let currentAudio = null;    // Audio currently playing
let lastVoiceAt = 0;        // anti-spam timestamp

// Configure your OGG files here (add more files freely)
const AUDIO = {
  start:  ["start_01.ogg", "start_02.ogg", "start_03.ogg", "start_04.ogg", "start_05.ogg"],
  look:   ["look_01.ogg", "look_02.ogg", "look_03.ogg"],
  choose: ["choose_01.ogg", "choose_02.ogg"],
  good:   ["good_01.ogg", "good_02.ogg", "good_03.ogg"],
  almost: ["almost_01.ogg", "almost_02.ogg", "almost_03.ogg"],
  finish: ["finish_01.ogg", "finish_02.ogg", "finish_03.ogg"],
  reward: ["reward_01.ogg"]
};

// Optional: separate small SFX (can be same OGG format)
const SFX = {
  ding: ["ding_01.ogg"], // short "дзынь" (optional)
};

function loadSoundPref() {
  const v = localStorage.getItem("rg_sound_on");
  soundOn = (v === null) ? true : (v === "1");

  const m = localStorage.getItem("rg_voice_mode");
  voiceMode = (m === "full" || m === "soft") ? m : "soft";

  renderSoundIcon();
}

function renderSoundIcon() {
  const btn = $("btnSound");
  if (!btn) return;
  btn.textContent = soundOn ? "🔊" : "🔇";
  btn.title = soundOn ? "Звук включён" : "Звук выключен";
}

window.toggleSound = function() {
  soundOn = !soundOn;
  localStorage.setItem("rg_sound_on", soundOn ? "1" : "0");
  renderSoundIcon();
};

// priority:
// - "voice" lines: do not interrupt by default
// - "sfx" can play on top (via separate Audio object)
function stopAudio(force = false) {
  if (currentAudio) {
    if (force) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
  }
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// Non-interrupting voice line by default.
// If you want to force-play (interrupt), pass {interrupt:true}.
function playVoice(type, opts = {}) {
  if (!soundOn) return Promise.resolve();

  const list = AUDIO[type];
  if (!list || !list.length) return Promise.resolve();

  const interrupt = !!opts.interrupt;

  if (!interrupt && currentAudio && !currentAudio.ended) {
    return Promise.resolve(); // не перебиваем
  }

  const file = pick(list);
  const key = `${type}/${file}`;

  if (!audioCache[key]) {
    const a = new Audio(`/static/audio/${type}/${file}`);
    a.preload = "auto";
    audioCache[key] = a;
  }

  if (interrupt && currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
  }

  currentAudio = audioCache[key];
  currentAudio.currentTime = 0;

  return new Promise(resolve => {
    currentAudio.onended = () => {
      resolve();
    };
    currentAudio.play().catch(() => resolve());
  });
}

// SFX can overlap voice (uses separate Audio instance, no caching needed but we can)
function playSfx(type) {
  if (!soundOn) return;
  const list = SFX[type];
  if (!list || !list.length) return;
  const file = pick(list);
  const a = new Audio(`/static/audio/sfx/${type}/${file}`); // expected path for sfx
  a.preload = "auto";
  a.play().catch(() => {});
}

// Hint policy (soft mode)
function shouldHintLook(i) {
  if (voiceMode === "full") return true;
  return i < 2 || (i % 4 === 3);
}
function shouldHintChoose(i) {
  if (voiceMode === "full") return true;
  return i < 2 || (i % 4 === 3);
}

// ===================== UI helpers =====================
function setPill(text) {
  const el = $("pillStatus");
  if (el) el.textContent = text;
}
function setToast(text) {
  const el = $("toast");
  if (el) el.textContent = text || "";
}
function setProgress(p) {
  const el = $("progressBar");
  if (el) el.style.width = `${Math.max(0, Math.min(100, p))}%`;
}
function setRingVisible(v) {
  const el = $("timerRing");
  if (el) el.style.display = v ? "block" : "none";
}
function setRingProgress(p) {
  const el = $("timerRing");
  if (!el) return;
  const deg = Math.max(0, Math.min(1, p)) * 360;
  el.style.background = `conic-gradient(var(--primary) ${deg}deg, #E5E7EB 0deg)`;
}
function clearTimers() {
  if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
  if (ringTimer) { clearInterval(ringTimer); ringTimer = null; }
}
function renderLives() {
  const el = document.getElementById("livesHud");
  if (!el) return;

  if (gameMode !== "survival") {
    el.style.display = "none";
    el.textContent = "";
    return;
  }

  el.style.display = "block";
  el.textContent =
    "Жизни: " +
    "❤".repeat(Math.max(0, livesLeft)) +
    "♡".repeat(Math.max(0, livesStart - livesLeft));
}
// ===================== Children =====================
async function createChild() {
  const nameEl = $("childName");
  if (!nameEl) return;

  const name = nameEl.value.trim();
  if (!name) return alert("Введите имя");

  await api("/api/children", {
    method: "POST",
    body: JSON.stringify({ name })
  });

  nameEl.value = "";
  await loadChildren();
}

async function loadChildren() {
  const sel = $("childSelect");
  if (!sel) return;

  const list = await api("/api/children");
  sel.innerHTML = "";

  list.forEach(c => {
    const opt = document.createElement("option");
    opt.textContent = c.name;   // показываем только название
    opt.value = String(c.id);
    sel.appendChild(opt);
  });
  // выбрать первый элемент по умолчанию и обновить кастомный селект
  if (sel.options.length > 0) sel.value = sel.options[0].value;
  sel.dispatchEvent(new Event("change", { bubbles: true }));
}

// ===================== Game flow =====================
function resetUI() {
  clearTimers();
  stopAudio(false);

  const options = $("options");
  if (options) options.innerHTML = "";

  const word = $("word");
  if (word) word.classList.add("hidden");

  setRingVisible(false);
  setToast("");
  setProgress(0);

  const sInfo = $("sessionInfo");
  if (sInfo) sInfo.textContent = "Сессия: —";
  const spInfo = $("speedInfo");
  if (spInfo) spInfo.textContent = "Показ: — мс";

  const btnRestart = $("btnRestart");
  if (btnRestart) btnRestart.disabled = true;
  const btnPlay = $("btnPlay");
  if (btnPlay) btnPlay.disabled = false;

  livesStart = 0;
  livesLeft = 0;
  renderLives();

  setPill("Готово");
}

function restart() {
  session = null;
  items = [];
  idx = 0;
  gameMode = "word_flash";
  livesStart = 0;
  livesLeft = 0;

  survStartedAtMs = 0;
  survCorrect = 0;
  survWrong = 0;
  survStreak = 0;
  survBestStreak = 0;
  survDead = false;

  const emptyHint = document.getElementById("resultEmptyHint");
  if (emptyHint) emptyHint.style.display = "block";

  const sr = document.getElementById("survivalResult");
  if (sr) sr.style.display = "none";
  const rb = $("resultBlock");
  if (rb) rb.style.display = "none";

  resetUI();
}

async function start() {
  const sel = $("childSelect");
  if (!sel) return;

  const themeId = parseInt(document.getElementById("themeSelect")?.value || "1", 10);
  localStorage.setItem("rg_theme_id", String(themeId));

  const childId = parseInt(sel.value || "0", 10);
  if (!childId) return alert("Выберите профиль ребёнка");

  const difficulty = document.getElementById("difficultySelect")?.value || "normal";

  resetUI();
  setPill("Загрузка…");

  const btnPlay = $("btnPlay");
  if (btnPlay) btnPlay.disabled = true;

  // объявляем mode ОДИН раз
  const mode = window.rg_selected_mode || "word_flash";

  // запрос ОДИН раз
  const data = await api("/api/sessions/start", {
    method: "POST",
    body: JSON.stringify({
      child_id: childId,
      mode: mode,
      difficulty: difficulty,
      theme_id: themeId
    })
  });

// присваивания ОДИН раз
session = data;
items = data.items;
idx = 0;

  gameMode = data.mode || mode;

  // init survival
  if (gameMode === "survival") {
    livesStart = data.lives_start || 3;
    livesLeft = data.lives_left || livesStart;

    survStartedAtMs = performance.now();
    survCorrect = 0;
    survWrong = 0;
    survStreak = 0;
    survBestStreak = 0;
    survDead = false;

    const sr = document.getElementById("survivalResult");
    if (sr) sr.style.display = "block";
  } else {
    const sr = document.getElementById("survivalResult");
    if (sr) sr.style.display = "none";
  }

  renderLives();
  const sInfo = $("sessionInfo");
  if (sInfo) sInfo.textContent = `Сессия: #${data.session_id}`;
  const spInfo = $("speedInfo");
  if (spInfo) spInfo.textContent = `Показ: ${data.exposure_ms} мс`;

  const btnRestart = $("btnRestart");
  if (btnRestart) btnRestart.disabled = false;

  setPill("Играй");

  // Start voice (interrupt ok)
  await playVoice("start", { interrupt: true });

  nextItem();
}

async function nextItem() {
  if (!items || idx >= items.length) return finish();

  const it = items[idx];
    resetOptionsUI();
    clearTimers();
   if (gameMode === "letter_builder") lbReset();
  // UI baseline
  const optionsEl = $("options");
    if (optionsEl) optionsEl.classList.remove("lettersGrid");

    const wordEl = $("word");
    if (wordEl) wordEl.classList.remove("typedWord");

// ======= ODD ONE OUT: без фазы "показа слова", подсказка не скрывается =======
if (gameMode === "odd_one_out") {
  clearTimers();
  setRingVisible(false);

  if (wordEl) {
    wordEl.textContent = (it.prompt ?? "Выбери лишнее слово:");
    wordEl.classList.remove("hidden");
  }

  setToast("");
  if (shouldHintChoose(idx)) await playVoice("choose");

  renderOptions(it);

  // старт реакции после реальной отрисовки вариантов
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      shownAt = performance.now();
    });
  });

  return;
}
 // ======= LETTER BUILDER: без подсказок и без показа правильного слова =======
  if (gameMode === "letter_builder") {
    clearTimers();
    setRingVisible(false);

    // В основном поле показываем то, что ребёнок собрал (пока пусто)
    if (wordEl) {
      wordEl.textContent = lbTyped || " ";
      wordEl.classList.remove("hidden");
    }

    // Никаких подсказок / тостов
    setToast("");

    // Рисуем "options" как БУКВЫ
    renderOptions(it);

    // Старт реакции после фактической отрисовки
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        shownAt = performance.now();
      });
    });

    return;
  }

 // ======= VOCAB SPELL: слово с пропуском + варианты букв =======
if (gameMode === "vocab_spell") {
  clearTimers();
  setRingVisible(false);

  if (wordEl) {
    wordEl.textContent = (it.prompt ?? "");
    wordEl.classList.remove("hidden");
  }

  setToast(choosePromptForMode(gameMode));

  if (shouldHintChoose(idx)) await playVoice("choose");

  renderOptions(it);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      shownAt = performance.now();
    });
  });

  return;
}
  // ======= Обычные режимы (word_flash / survival) =======
  setToast("Смотри на слово…");

  // Soft hints
  if (shouldHintLook(idx)) {
    await playVoice("look");
  }

  // Show word
  if (wordEl) {
    wordEl.textContent = (it.prompt ?? it.target ?? "");
    wordEl.classList.remove("hidden");
  }

  setRingVisible(true);
  setRingProgress(0);

  clearTimers();

  // Ring animation
  const startT = performance.now();
  ringTimer = setInterval(() => {
    const p = (performance.now() - startT) / it.exposure_ms;
    setRingProgress(p);
    if (p >= 1) {
      clearInterval(ringTimer);
      ringTimer = null;
    }
  }, 16);

  // After exposure_ms: hide word, show options
  hideTimer = setTimeout(async () => {
    if (wordEl) wordEl.classList.add("hidden");
    setRingVisible(false);

    setToast(choosePromptForMode(gameMode));
    if (shouldHintChoose(idx)) await playVoice("choose");
    resetOptionsUI();
    renderOptions(it);
    // фиксируем старт реакции после реальной отрисовки
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        shownAt = performance.now();
      });
    });
  }, it.exposure_ms);
}

function renderOptions(it){
  const optionsEl = $("options");
  if(!optionsEl) return;

  // === ВАЖНО: включаем сетку плиток только для letter_builder ===
  if (gameMode === "letter_builder") optionsEl.classList.add("lettersGrid");
  else optionsEl.classList.remove("lettersGrid");

  optionsEl.innerHTML = "";

  // ===== letter_builder: options = буквы =====
  if (gameMode === "letter_builder") {
    const wordEl = $("word");
    const right = (it.correct ?? it.target ?? "");
    const needLen = right.length;

    it.options.forEach(ch => {
      const btn = document.createElement("button");
      btn.className = "opt";
      btn.textContent = ch;

      btn.onclick = async () => {
        if (lbLocked) return;

        // нажали букву -> добавили, кнопку выключили
        btn.disabled = true;
        lbTyped += ch;

        if (wordEl) wordEl.textContent = lbTyped || " ";

        // набрали длину слова -> отправляем в стандартный answer()
        if (lbTyped.length >= needLen) {
          lbLocked = true;
          await answer(it, lbTyped, null);
        }
      };

      optionsEl.appendChild(btn);
    });

    return;
  }

  // ===== обычные режимы: options = слова =====
  it.options.forEach(opt => {
    const btn = document.createElement("button");
    btn.className = "opt";
    btn.textContent = opt;
    btn.onclick = () => answer(it, opt, btn);
    optionsEl.appendChild(btn);
  });
}

async function answer(it, chosen, btnEl) {
  const t = performance.now();
  const reaction = Math.round(t - shownAt);
  const right = (it.correct ?? it.target);
  const correct = (chosen === right);
  if (gameMode === "survival") {
  if (correct) {
    survCorrect += 1;
    survStreak += 1;
    if (survStreak > survBestStreak) survBestStreak = survStreak;
  } else {
    survWrong += 1;
    survStreak = 0;
  }
}
  // Lock buttons
  const allBtns = [...document.querySelectorAll("#options .opt")];
  allBtns.forEach(b => b.disabled = true);

  // Mark chosen
  if (btnEl) btnEl.classList.add(correct ? "ok" : "bad");

  // Mark correct if wrong
  if (!correct) {
    const rightValue = (it.correct ?? it.target);
    const rightBtn = allBtns.find(b => b.textContent === rightValue);
    if (rightBtn) rightBtn.classList.add("ok");
  }

  // Send attempt
  const attemptResp = await api(`/api/sessions/${session.session_id}/attempt`, {
  method: "POST",
  body: JSON.stringify({
    item_id: it.item_id,
    correct: correct,
    reaction_ms: reaction,
    shown_ms: it.exposure_ms
  })
});
  if (gameMode === "survival") {
  if (typeof attemptResp.lives_left === "number") livesLeft = attemptResp.lives_left;

  if (attemptResp.finished) {
    survDead = true;     // умер по жизням
    // покажем результат сразу, без nextItem()
    return finish();
  }
}
  // ===== SURVIVAL логика =====
if (gameMode === "survival") {
  if (typeof attemptResp.lives_left === "number") {
    livesLeft = attemptResp.lives_left;
    renderLives();
  }

  if (attemptResp.finished) {
    // Немедленно завершаем игру
    await playVoice("finish", { interrupt: true });
    return finish();
  }
}
 // Feedback
  setPill(correct ? "Верно" : "Почти");
  setToast(`${correct ? "Правильно" : "Почти"} • ${reaction} мс`);

  // Voice feedback
  await playVoice(correct ? "good" : "almost");

  // Для словарного режима показываем:
  // неверную букву -> правильную букву
  if (gameMode === "vocab_spell") {
    await animateVocabReveal(it, chosen, correct);
  }

  idx += 1;
  setProgress((idx / items.length) * 100);

  setTimeout(() => {
    setPill("Играй");
    nextItem();
  }, gameMode === "vocab_spell" ? 420 : 450);
}

function starsFromAccuracy(acc) {
  if (acc >= 0.85) return 3;
  if (acc >= 0.70) return 2;
  return 1;
}

function renderResult(out) {
  const rb = $("resultBlock");
  if (rb) rb.style.display = "block";

  const stars = starsFromAccuracy(out.accuracy);
  const starsWrap = $("stars");
  if (starsWrap) {
    const starEls = [...starsWrap.querySelectorAll(".star")];
    starEls.forEach((s, i) => s.classList.toggle("on", i < stars));
  }

  const acc = $("kpiAcc");
  if (acc) acc.textContent = `${Math.round(out.accuracy * 100)}%`;
  const react = $("kpiReact");
  if (react) react.textContent = `${Math.round(out.avg_reaction_ms)} мс`;
  const next = $("kpiNext");
  if (next) next.textContent = `${out.next_exposure_ms} мс`;
}

function renderSurvivalResult() {
  const sr = document.getElementById("survivalResult");
  if (!sr) return;
  sr.style.display = "block";

  const durationSec = survStartedAtMs
    ? Math.max(0, (performance.now() - survStartedAtMs) / 1000)
    : 0;

  const kLives = document.getElementById("kpiLives");
  if (kLives) kLives.textContent = `${Math.max(0, livesLeft)} / ${Math.max(0, livesStart)}`;

  const kTime = document.getElementById("kpiTime");
  if (kTime) kTime.textContent = `${Math.round(durationSec)} сек`;

  const kStreak = document.getElementById("kpiStreak");
  if (kStreak) kStreak.textContent = `${survBestStreak}`;

  const kWrong = document.getElementById("kpiWrong");
  if (kWrong) kWrong.textContent = `${survWrong}`;

  const reason = document.getElementById("survivalEndReason");
  if (reason) {
    if (survDead) reason.textContent = "Игра окончена: закончились жизни.";
    else if (items && idx >= items.length) reason.textContent = "Тренировка завершена: слова закончились.";
    else reason.textContent = "Тренировка завершена.";
  }
}

async function finish() {
  clearTimers();

  const optionsEl = $("options");
  if (optionsEl) optionsEl.innerHTML = "";

  const wordEl = $("word");
  if (wordEl) wordEl.classList.add("hidden");

  setRingVisible(false);
  setToast("Считаю результат…");
  setPill("Готово");

  const out = await api(`/api/sessions/${session.session_id}/finish`, { method: "POST" });

  setToast("Тренировка закончилась. Можно сыграть ещё раз.");
  renderResult(out);
  if (out.new_achievements && out.new_achievements.length) {
  showAchievements(out.new_achievements);
}
  const emptyHint = document.getElementById("resultEmptyHint");
  if (emptyHint) emptyHint.style.display = "none";
  if (gameMode === "survival") {
  renderSurvivalResult(out);
}

  // Finish voice line (interrupt ok, it's important)
  await playVoice("finish", { interrupt: true });

  const btnPlay = document.getElementById("btnPlay");
if (btnPlay) btnPlay.disabled = false;

  // If you have a "reward" screen later, call: playVoice("reward")
}

// ===================== Init =====================
(function init() {
  loadSoundPref();
  loadThemes().catch(() => {});
  loadChildren().catch(() => {});
  resetUI();
})();

function resetOptionsUI() {
  const optionsEl = $("options");
  if (!optionsEl) return;

  // убрать старые кнопки
  optionsEl.innerHTML = "";

  // убрать режимные классы (на случай, если их где-то добавляли)
  optionsEl.classList.remove("lettersGrid");

  // если у тебя есть скрытие через класс/атрибут — сбрось тут
  optionsEl.classList.remove("hidden");
}

async function animateVocabReveal(item, chosen, isCorrect) {
  const wordEl = $("word");
  if (!wordEl) return;

  const masked = item.prompt ?? "";
  const right = item.correct ?? "";
  const missIdx = masked.indexOf("_");

  if (missIdx < 0 || !right) {
    wordEl.textContent = masked;
    return;
  }

  const before = masked.slice(0, missIdx);
  const after = masked.slice(missIdx + 1);

  const renderState = (letter, cls) => {
    wordEl.innerHTML = `
      <span>${before}</span><span class="reveal-letter ${cls}">${letter}</span><span>${after}</span>
    `;
  };

  // Сброс состояний
  wordEl.classList.remove("revealWord", "revealWordBad", "revealWordGood");

  if (isCorrect) {
    renderState(right, "reveal-good");
    wordEl.classList.add("revealWordGood");
    await new Promise(resolve => setTimeout(resolve, 550));
  } else {
    // 1. Показываем выбранную букву красным
    renderState(chosen, "reveal-bad");
    wordEl.classList.add("revealWordBad");
    await new Promise(resolve => setTimeout(resolve, 320));

    // 2. Меняем на правильную букву золотым
    wordEl.classList.remove("revealWordBad");
    renderState(right, "reveal-good");
    wordEl.classList.add("revealWordGood");
    await new Promise(resolve => setTimeout(resolve, 520));
  }

  // 3. Фиксируем итоговое слово обычным текстом
  const fullWord = before + right + after;
  wordEl.textContent = fullWord;
  wordEl.classList.remove("revealWord", "revealWordBad", "revealWordGood");
}

function revealVocabWord(item, chosen, correct) {
  const wordEl = $("word");
  if (!wordEl) return Promise.resolve();

  const masked = item.prompt ?? "";
  const right = item.correct ?? "";
  const missIdx = masked.indexOf("_");

  if (missIdx < 0 || !right) {
    wordEl.textContent = masked;
    return Promise.resolve();
  }

  const fullWord = masked.slice(0, missIdx) + right + masked.slice(missIdx + 1);

  // Сбрасываем предыдущее состояние
  wordEl.classList.remove("revealWord", "revealWordBad");

  // Рисуем слово так, чтобы новая буква была отдельным span
  const before = masked.slice(0, missIdx);
  const after = masked.slice(missIdx + 1);

  wordEl.innerHTML = `
    <span>${before}</span><span class="reveal-letter">${right}</span><span>${after}</span>
  `;

  // Если ответ был неверный — можно слегка выделить раскрытие
  if (!correct) {
    wordEl.classList.add("revealWordBad");
  } else {
    wordEl.classList.add("revealWord");
  }

  return new Promise(resolve => {
    setTimeout(() => {
      wordEl.textContent = fullWord;
      wordEl.classList.remove("revealWord", "revealWordBad");
      resolve();
    }, 550);
  });
}

function showAchievements(list){
  const wrap = document.createElement("div");
  wrap.style.position = "fixed";
  wrap.style.top = "20px";
  wrap.style.right = "20px";
  wrap.style.zIndex = "99999";

  list.forEach(a => {
    const el = document.createElement("div");
    el.style.background = "rgba(10,10,20,.95)";
    el.style.color = "#fff";
    el.style.padding = "14px 18px";
    el.style.borderRadius = "14px";
    el.style.marginBottom = "10px";
    el.style.boxShadow = "0 0 30px rgba(212,175,55,.35)";
    el.innerHTML = `
      <div style="font-size:22px">${a.icon} ${a.title}</div>
      <div style="opacity:.8;font-size:14px">${a.description}</div>
    `;
    wrap.appendChild(el);
  });

  document.body.appendChild(wrap);
  setTimeout(()=>wrap.remove(), 4500);
}