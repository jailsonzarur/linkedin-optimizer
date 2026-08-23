document.addEventListener("alpine:init", () => {
  Alpine.data("composer", () => ({
    blocks: [],
    nextId: 1,

    addText() {
      this.blocks.push({ id: this.nextId++, type: "text" });
    },

    addAudio() {
      if (this.hasAudioBlock) return;
      this.blocks.push({ id: this.nextId++, type: "audio" });
    },

    remove(id) {
      this.blocks = this.blocks.filter((block) => block.id !== id);
    },

    get hasAudioBlock() {
      return this.blocks.some((block) => block.type === "audio");
    },
  }));

  Alpine.data("audioBlock", () => ({
    items: [],
    recording: false,
    elapsed: 0,
    error: "",
    recorder: null,
    chunks: [],
    timer: null,

    destroy() {
      this.items.forEach((item) => URL.revokeObjectURL(item.url));
      clearInterval(this.timer);
    },

    get canRecord() {
      return Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
    },

    push(file, recorded) {
      this.items.push({
        key: `${Date.now()}-${Math.random()}`,
        file,
        name: file.name,
        size: file.size,
        url: URL.createObjectURL(file),
        recorded,
      });
      this.sync();
    },

    addFiles(fileList) {
      for (const file of fileList) this.push(file, false);
    },

    async toggleRecording() {
      if (this.recording) {
        this.stopRecording();
        return;
      }

      this.error = "";
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.chunks = [];
        this.recorder = new MediaRecorder(stream);

        this.recorder.ondataavailable = (event) => {
          if (event.data.size) this.chunks.push(event.data);
        };

        this.recorder.onstop = () => {
          const mime = this.recorder.mimeType || "audio/webm";
          const blob = new Blob(this.chunks, { type: mime });
          this.push(
            new File([blob], `recording-${Date.now()}.${this.extensionFor(mime)}`, { type: mime }),
            true,
          );
          stream.getTracks().forEach((track) => track.stop());
        };

        this.recorder.start();
        this.recording = true;
        this.elapsed = 0;
        this.timer = setInterval(() => this.elapsed++, 1000);
      } catch {
        this.error = "Could not access the microphone. Check your browser permission.";
      }
    },

    stopRecording() {
      if (!this.recorder || !this.recording) return;
      this.recorder.stop();
      this.recording = false;
      clearInterval(this.timer);
    },

    remove(key) {
      const item = this.items.find((candidate) => candidate.key === key);
      if (item) URL.revokeObjectURL(item.url);
      this.items = this.items.filter((candidate) => candidate.key !== key);
      this.sync();
    },

    sync() {
      const transfer = new DataTransfer();
      this.items.forEach((item) => transfer.items.add(item.file));
      this.$refs.input.files = transfer.files;
    },

    extensionFor(mime) {
      if (mime.includes("mp4")) return "m4a";
      if (mime.includes("ogg")) return "ogg";
      if (mime.includes("wav")) return "wav";
      return "webm";
    },

    formatSize(bytes) {
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },

    formatTime(seconds) {
      const m = String(Math.floor(seconds / 60)).padStart(2, "0");
      const s = String(seconds % 60).padStart(2, "0");
      return `${m}:${s}`;
    },
  }));
});
