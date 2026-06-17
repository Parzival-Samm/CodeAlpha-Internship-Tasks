import threading
import datetime
import customtkinter as ctk
from deep_translator import GoogleTranslator
import pyperclip

# --- Configuration & Styling (Material 3 Minimalist) ---
ctk.set_appearance_mode("Light")  # Light mode by default as per spec
ctk.set_default_color_theme("blue")

# Custom Colors mapping (Light Mode, Dark Mode)
BG_COLOR = ("#F8FAFC", "#0F172A")          # Clean off-white / Deep slate
CARD_COLOR = ("#FFFFFF", "#1E293B")        # Pure white / Dark slate
ACCENT_COLOR = ("#4F8EF7", "#4F8EF7")      # Gradient Blue equivalent
TEXT_PRIMARY = ("#0F172A", "#F8FAFC")
TEXT_SECONDARY = ("#64748B", "#94A3B8")

LANGUAGES = {
    "Auto Detect": "auto", "English": "en", "Spanish": "es", 
    "French": "fr", "German": "de", "Urdu": "ur", 
    "Arabic": "ar", "Hindi": "hi", "Chinese": "zh-CN", 
    "Japanese": "ja", "Russian": "ru"
}

class LinguaFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("LinguaFlow Translator")
        self.geometry("500x800") # Mobile-proportions for desktop
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.history_data = []

        self.create_ui()

    def create_ui(self):
        # --- Top Navigation Bar ---
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.nav_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.logo_label = ctk.CTkLabel(
            self.nav_frame, text="🌐 LinguaFlow", 
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.logo_label.pack(side="left")

        self.theme_btn = ctk.CTkButton(
            self.nav_frame, text="🌓", width=40, fg_color="transparent", 
            text_color=TEXT_PRIMARY, hover_color=CARD_COLOR, command=self.toggle_theme
        )
        self.theme_btn.pack(side="right")

        # --- Language Selection Row ---
        self.lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lang_frame.pack(fill="x", padx=20, pady=10)

        self.src_lang = ctk.CTkComboBox(
            self.lang_frame, values=list(LANGUAGES.keys()), width=180,
            fg_color=CARD_COLOR, border_color=CARD_COLOR, dropdown_fg_color=CARD_COLOR, 
            text_color=TEXT_PRIMARY, font=("Inter", 14), corner_radius=12
        )
        self.src_lang.set("Auto Detect")
        self.src_lang.pack(side="left")

        self.swap_btn = ctk.CTkButton(
            self.lang_frame, text="⇅", width=40, height=40, corner_radius=20,
            fg_color=CARD_COLOR, text_color=ACCENT_COLOR, hover_color=BG_COLOR,
            font=("Inter", 18, "bold"), command=self.swap_languages
        )
        self.swap_btn.pack(side="left", expand=True)

        self.target_lang = ctk.CTkComboBox(
            self.lang_frame, values=[k for k in LANGUAGES.keys() if k != "Auto Detect"], width=180,
            fg_color=CARD_COLOR, border_color=CARD_COLOR, dropdown_fg_color=CARD_COLOR, 
            text_color=TEXT_PRIMARY, font=("Inter", 14), corner_radius=12
        )
        self.target_lang.set("Spanish")
        self.target_lang.pack(side="right")

        # --- Text Input Card ---
        self.input_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=16)
        self.input_frame.pack(fill="x", padx=20, pady=10)

        self.input_textbox = ctk.CTkTextbox(
            self.input_frame, height=100, fg_color="transparent", 
            text_color=TEXT_PRIMARY, font=("Inter", 16)
        )
        self.input_textbox.pack(fill="both", padx=10, pady=10)
        self.input_textbox.insert("1.0", "Enter text to translate...")
        self.input_textbox.bind("<FocusIn>", self.clear_placeholder)

        self.input_tools = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.input_tools.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(self.input_tools, text="❌ Clear", width=60, fg_color="transparent", text_color=TEXT_SECONDARY, hover_color=BG_COLOR, command=self.clear_input).pack(side="left")
        ctk.CTkButton(self.input_tools, text="📋 Paste", width=60, fg_color="transparent", text_color=TEXT_SECONDARY, hover_color=BG_COLOR, command=self.paste_input).pack(side="left")

        # --- Primary Translate Button ---
        self.translate_btn = ctk.CTkButton(
            self, text="Translate", height=50, corner_radius=25,
            fg_color=ACCENT_COLOR, text_color="#FFFFFF", font=("Inter", 16, "bold"),
            command=self.start_translation
        )
        self.translate_btn.pack(fill="x", padx=20, pady=15)

        # --- Output Card ---
        self.output_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=16)
        self.output_frame.pack(fill="x", padx=20, pady=5)

        self.output_textbox = ctk.CTkTextbox(
            self.output_frame, height=100, fg_color="transparent", 
            text_color=TEXT_PRIMARY, font=("Inter", 16), state="disabled"
        )
        self.output_textbox.pack(fill="both", padx=10, pady=10)

        self.output_tools = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        self.output_tools.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(self.output_tools, text="📋", width=40, fg_color="transparent", text_color=ACCENT_COLOR, hover_color=BG_COLOR, font=("Inter", 16), command=self.copy_output).pack(side="right")
        ctk.CTkButton(self.output_tools, text="❤️", width=40, fg_color="transparent", text_color=ACCENT_COLOR, hover_color=BG_COLOR, font=("Inter", 16), command=self.save_to_history).pack(side="right")

        # --- History Section ---
        self.history_label = ctk.CTkLabel(self, text="Recent Translations", font=("Inter", 14, "bold"), text_color=TEXT_SECONDARY)
        self.history_label.pack(anchor="w", padx=25, pady=(20, 5))

        self.history_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=150)
        self.history_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # --- Core Functionality ---
    
    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Dark" if current == "Light" else "Light")

    def clear_placeholder(self, event):
        if self.input_textbox.get("1.0", "end-1c").strip() == "Enter text to translate...":
            self.input_textbox.delete("1.0", "end")

    def clear_input(self):
        self.input_textbox.delete("1.0", "end")

    def paste_input(self):
        self.clear_input()
        self.input_textbox.insert("1.0", pyperclip.paste())

    def swap_languages(self):
        src = self.src_lang.get()
        tgt = self.target_lang.get()
        if src != "Auto Detect":
            self.src_lang.set(tgt)
            self.target_lang.set(src)

    def copy_output(self):
        pyperclip.copy(self.output_textbox.get("1.0", "end-1c").strip())
        self.translate_btn.configure(text="Copied Successfully!", fg_color="#10B981")
        self.after(2000, lambda: self.translate_btn.configure(text="Translate", fg_color=ACCENT_COLOR))

    def start_translation(self):
        threading.Thread(target=self.process_translation, daemon=True).start()

    def process_translation(self):
        text = self.input_textbox.get("1.0", "end-1c").strip()
        if not text or text == "Enter text to translate...":
            return

        self.translate_btn.configure(text="Translating...", state="disabled")
        
        src = LANGUAGES.get(self.src_lang.get(), "auto")
        tgt = LANGUAGES.get(self.target_lang.get(), "en")

        try:
            result = GoogleTranslator(source=src, target=tgt).translate(text)
            
            self.output_textbox.configure(state="normal")
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("1.0", result)
            self.output_textbox.configure(state="disabled")
        except Exception:
            self.translate_btn.configure(text="⚠️ Translation Failed", fg_color="#EF4444")
            self.after(3000, lambda: self.translate_btn.configure(text="Translate", fg_color=ACCENT_COLOR))
        finally:
            if self.translate_btn.cget("text") == "Translating...":
                self.translate_btn.configure(text="Translate", state="normal")

    def save_to_history(self):
        src = self.input_textbox.get("1.0", "end-1c").strip()
        tgt = self.output_textbox.get("1.0", "end-1c").strip()
        if not src or not tgt or src == "Enter text to translate...": return

        # Build history card
        card = ctk.CTkFrame(self.history_scroll, fg_color=CARD_COLOR, corner_radius=8)
        card.pack(fill="x", pady=5)
        
        ctk.CTkLabel(card, text=f"{self.src_lang.get()} → {self.target_lang.get()}", font=("Inter", 11, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=10, pady=(5,0))
        ctk.CTkLabel(card, text=src, font=("Inter", 12), text_color=TEXT_SECONDARY).pack(anchor="w", padx=10)
        ctk.CTkLabel(card, text=tgt, font=("Inter", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(0,5))


if __name__ == "__main__":
    app = LinguaFlowApp()
    app.mainloop()