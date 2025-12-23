const { createApp, ref, computed, onMounted } = Vue;

createApp({
  setup() {
    const notes = ref([]);
    const loading = ref(false);
    const error = ref("");

    const showEditor = ref(false);
    const editingNote = ref(null);

    const title = ref("");
    const content = ref("");
    const color = ref("#FFE57F");
    const images = ref([]); // File objects
    const existingUrls = ref([]);
    const deletedUrls = ref([]);

    const titleCount = computed(() => title.value.length);
    const contentCount = computed(() => content.value.length);

    const colors = [
      "#FFE57F",
      "#FFB3BA",
      "#BAE1FF",
      "#BAFFC9",
      "#E0BBE4",
      "#FFDAC1",
    ];

    const fetchNotes = async () => {
      loading.value = true;
      try {
        const res = await fetch("/api/notes");
        if (!res.ok) throw new Error("Failed to load notes");
        notes.value = await res.json();
      } catch (e) {
        error.value = e.message || "Error";
      } finally {
        loading.value = false;
      }
    };

    const openCreate = () => {
      editingNote.value = null;
      title.value = "";
      content.value = "";
      color.value = "#FFE57F";
      images.value = [];
      existingUrls.value = [];
      deletedUrls.value = [];
      showEditor.value = true;
    };

    const openEdit = (note) => {
      editingNote.value = note;
      title.value = note.title;
      content.value = note.content;
      color.value = note.color;
      images.value = [];
      existingUrls.value = [...(note.image_urls || [])];
      deletedUrls.value = [];
      showEditor.value = true;
    };

    const closeEditor = () => {
      showEditor.value = false;
    };

    const onFileChange = (event) => {
      const files = Array.from(event.target.files || []);
      const all = [...images.value, ...files];
      if (all.length > 3) {
        alert("最多 3 张图片");
        return;
      }
      const tooBig = all.find((f) => f.size > 5 * 1024 * 1024);
      if (tooBig) {
        alert("单张图片不能超过 5MB");
        return;
      }
      images.value = all;
    };

    const removeExisting = (url) => {
      deletedUrls.value = [...deletedUrls.value, url];
      existingUrls.value = existingUrls.value.filter((u) => u !== url);
    };

    const removeNewFile = (idx) => {
      images.value = images.value.filter((_, i) => i !== idx);
    };

    const saveNote = async () => {
      if (!title.value || title.value.length > 30) return;
      if (!content.value || content.value.length > 500) return;

      const isEdit = !!editingNote.value;
      const url = isEdit ? `/api/notes/${editingNote.value.id}` : "/api/notes";
      const method = isEdit ? "PUT" : "POST";

      const form = new FormData();
      form.append("title", title.value);
      form.append("content", content.value);
      form.append("color", color.value);
      existingUrls.value.forEach((u) => form.append("existing_urls", u));
      deletedUrls.value.forEach((u) => form.append("deleted_urls", u));
      images.value.forEach((file) => form.append("images", file));

      try {
        const res = await fetch(url, { method, body: form });
        if (!res.ok) {
          const msg = (await res.json().catch(() => ({}))).error || "Save failed";
          throw new Error(msg);
        }
        await fetchNotes();
        closeEditor();
      } catch (e) {
        error.value = e.message || "Error";
      }
    };

    const deleteNote = async (note) => {
      if (!confirm("Are you sure you want to delete this note?")) return;
      try {
        const res = await fetch(`/api/notes/${note.id}`, {
          method: "DELETE",
        });
        if (!res.ok) throw new Error("Delete failed");
        await fetchNotes();
        closeEditor();
      } catch (e) {
        error.value = e.message || "Error";
      }
    };

    onMounted(fetchNotes);

    return {
      notes,
      loading,
      error,
      showEditor,
      editingNote,
      title,
      content,
      color,
      images,
      existingUrls,
      deletedUrls,
      titleCount,
      contentCount,
      colors,
      openCreate,
      openEdit,
      closeEditor,
      onFileChange,
      removeExisting,
      removeNewFile,
      saveNote,
      deleteNote,
    };
  },
  template: `
<div class="flex flex-col min-h-screen bg-slate-100">
  <header class="px-5 pt-4 pb-3 bg-slate-100 sticky top-0 z-10">
    <h1 class="text-xl font-semibold text-slate-900">ColorNote</h1>
  </header>

  <main class="flex-1 px-5 pb-24">
    <div v-if="loading" class="text-center text-slate-500 mt-8">Loading...</div>
    <div v-else-if="notes.length === 0" class="mt-16 text-center text-sm text-slate-400">
      No notes yet. Create your first note.
    </div>
    <div v-else class="space-y-4 mt-2">
      <article
        v-for="note in notes"
        :key="note.id"
        class="rounded-2xl p-4 shadow-sm cursor-pointer"
        :style="{ backgroundColor: note.color }"
        @click="openEdit(note)"
      >
        <h2 class="text-base font-semibold mb-1 break-words">
          {{ note.title }}
        </h2>
        <p class="text-sm text-slate-800 break-words line-clamp-3">
          {{ note.content }}
        </p>
      </article>
    </div>
  </main>

  <!-- Bottom create button -->
  <button
    class="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-sky-500 text-white text-3xl shadow-lg flex items-center justify-center"
    @click="openCreate"
  >
    +
  </button>

  <!-- Editor sheet -->
  <transition name="slide-up">
    <div
      v-if="showEditor"
      class="fixed inset-0 z-20 flex items-end justify-center"
    >
      <div class="absolute inset-0 bg-black/50" @click="closeEditor"></div>
      <div
        class="relative w-full max-w-md rounded-t-3xl p-4 pb-6"
        :style="{ backgroundColor: color }"
      >
        <header class="flex items-center justify-between mb-3">
          <h2 class="text-base font-semibold">
            {{ editingNote ? 'Edit note' : 'New note' }}
          </h2>
          <button
            v-if="editingNote"
            class="text-sm text-red-600"
            @click="deleteNote(editingNote)"
          >
            Delete
          </button>
        </header>

        <div class="space-y-3">
          <div>
            <input
              v-model="title"
              type="text"
              placeholder="Title"
              class="w-full bg-white/70 rounded-xl px-3 py-2 text-sm outline-none"
              :maxlength="30"
            />
            <div
              class="mt-1 text-xs text-right"
              :class="titleCount > 30 ? 'text-red-500' : 'text-slate-600'"
            >
              {{ titleCount }}/30
            </div>
          </div>

          <div>
            <textarea
              v-model="content"
              rows="4"
              placeholder="Write something..."
              class="w-full bg-white/70 rounded-xl px-3 py-2 text-sm outline-none resize-none"
              :maxlength="500"
            ></textarea>
            <div class="mt-1 text-xs text-right text-slate-600">
              {{ contentCount }}/500
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <span class="text-xs text-slate-800">Color</span>
            <div class="flex space-x-2">
              <button
                v-for="c in colors"
                :key="c"
                class="w-7 h-7 rounded-full border-2"
                :style="{ backgroundColor: c, borderColor: c === color ? '#0f172a' : 'transparent' }"
                @click="color = c"
              ></button>
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs text-slate-800">Images (max 3, ≤5MB)</span>
              <input type="file" accept="image/*" multiple @change="onFileChange" />
            </div>
            <div class="flex flex-wrap gap-2">
              <div
                v-for="url in existingUrls"
                :key="url"
                class="relative w-20 h-20 rounded-xl overflow-hidden bg-white/80"
              >
                <img :src="url" class="w-full h-full object-cover" />
                <button
                  class="absolute top-1 right-1 bg-black/60 text-white text-xs px-1 rounded"
                  @click.stop="removeExisting(url)"
                >
                  X
                </button>
              </div>
              <div
                v-for="(file, idx) in images"
                :key="file.name + idx"
                class="relative w-20 h-20 rounded-xl overflow-hidden bg-white/80 flex items-center justify-center text-xs text-slate-700"
              >
                {{ file.name }}
                <button
                  class="absolute top-1 right-1 bg-black/60 text-white text-xs px-1 rounded"
                  @click.stop="removeNewFile(idx)"
                >
                  X
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-end space-x-2">
          <button
            class="px-4 py-2 text-sm rounded-full bg-white/60 text-slate-800"
            @click="closeEditor"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 text-sm rounded-full bg-sky-600 text-white"
            @click="saveNote"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </transition>
</div>
`,
}).mount("#app");


