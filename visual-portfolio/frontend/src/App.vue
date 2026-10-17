<template>
  <router-view />
</template>

<style>
:root {
  --bg: #f5f7fb;
  --panel: #ffffff;
  --text: #17212b;
  --muted: #5a6b7b;
  --accent: #005f73;
  --line: #d6dde5;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  color: var(--text);
  background: radial-gradient(circle at top right, #e1f5f7, transparent 40%), var(--bg);
}

button, input, select {
  font: inherit;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
}
</style>
