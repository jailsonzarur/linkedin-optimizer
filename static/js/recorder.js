document.addEventListener("alpine:init", () => {
  Alpine.data("recorder", (postUrl, csrf) => ({
    supported: Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder),
    recording: false,
    uploading: false,
    elapsed: 0,
    error: "",
    recorder: null,
    stream: null,
    chunks: [],
    timer: null,
    audio: null,
    frame: null,

    destroy() {
      this.stop(true);
      clearInterval(this.timer);
      cancelAnimationFrame(this.frame);
    },

    async toggle() {
      if (this.recording) return this.stop();
      this.error = "";

      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        this.error = "Não consegui acessar o microfone. Verifique a permissão do navegador.";
        return;
      }

      this.chunks = [];
      this.recorder = new MediaRecorder(this.stream);
      this.recorder.ondataavailable = (event) => {
        if (event.data.size) this.chunks.push(event.data);
      };
      this.recorder.onstop = () => this.send();
      this.recorder.start();

      this.recording = true;
      this.elapsed = 0;
      this.timer = setInterval(() => this.elapsed++, 1000);
      this.draw();
    },

    stop(silent = false) {
      if (!this.recorder || !this.recording) return;
      this.recording = false;
      clearInterval(this.timer);
      cancelAnimationFrame(this.frame);
      if (silent) this.recorder.onstop = null;
      this.recorder.stop();
      this.stream.getTracks().forEach((track) => track.stop());
    },

    draw() {
      const canvas = this.$refs.wave;
      const context = canvas.getContext("2d");
      this.audio = new AudioContext();
      const analyser = this.audio.createAnalyser();
      analyser.fftSize = 256;
      this.audio.createMediaStreamSource(this.stream).connect(analyser);

      const bins = new Uint8Array(analyser.frequencyBinCount);
      const accent = getComputedStyle(document.documentElement)
        .getPropertyValue("--accent").trim();

      const paint = () => {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        analyser.getByteFrequencyData(bins);

        context.clearRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = accent;

        const bars = 40;
        const step = Math.floor(bins.length / bars);
        const width = canvas.width / bars;
        const middle = canvas.height / 2;

        for (let i = 0; i < bars; i++) {
          const value = bins[i * step] / 255;
          const height = Math.max(2, value * canvas.height * 0.9);
          context.globalAlpha = 0.35 + value * 0.65;
          context.fillRect(i * width, middle - height / 2, width - 2, height);
        }
        this.frame = requestAnimationFrame(paint);
      };
      paint();
    },

    async send() {
      const mime = this.recorder.mimeType || "audio/webm";
      const blob = new Blob(this.chunks, { type: mime });
      const form = new FormData();
      form.append("audio", blob, `answer-${Date.now()}.${this.extension(mime)}`);

      this.uploading = true;
      try {
        const response = await fetch(postUrl, {
          method: "POST",
          headers: { "X-CSRFToken": csrf },
          body: form,
        });
        if (!response.ok) throw new Error();
        this.$dispatch("answer-sent", await response.text());
      } catch {
        this.error = "Não consegui enviar o áudio. Tente de novo.";
      } finally {
        this.uploading = false;
      }
    },

    extension(mime) {
      if (mime.includes("mp4")) return "m4a";
      if (mime.includes("ogg")) return "ogg";
      return "webm";
    },

    get clock() {
      const m = String(Math.floor(this.elapsed / 60)).padStart(2, "0");
      const s = String(this.elapsed % 60).padStart(2, "0");
      return `${m}:${s}`;
    },
  }));
});
