import string
import time
import threading
import nltk
import customtkinter as ctk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure required NLTK resources are downloaded quietly (including punkt_tab fix)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

# ==========================================
# STEP 1: Expanded FAQ Dataset (Kept Exactly Same)
# ==========================================
FAQ_DATA = {
    "What is CodeAlpha and what do you do?": 
        "CodeAlpha is a virtual internship platform providing hands-on project experience in fields like software development, AI, cyber security, and data science.",
    "How long is the internship program?": 
        "The standard virtual internship cohort lasts for exactly 4 weeks (1 month).",
    "How do I get my completion certificate?": 
        "Upon successful submission and review of all your assigned tasks before the deadline, your completion certificate will be emailed to you.",
    "Where should I submit my tasks?": 
        "You must host all your code in a public GitHub repository. You will submit the repository link along with a short video demonstration of the project.",
    "What should be included in the video demonstration?": 
        "Your video should be 2-3 minutes long, showcasing your code structure, explaining the logic briefly, and demonstrating the final output running successfully.",
    "Can I get an extension if I miss a deadline?": 
        "Deadlines are generally flexible within the 4-week window, but all final tasks must be submitted before the official end date of your cohort.",
    "Is this a paid internship? Do I get a stipend?": 
        "No, this is an unpaid, educational virtual internship focused on skill-building and portfolio development.",
    "Who do I contact if I am stuck on a technical task?": 
        "Since this is an independent project-based internship, you are encouraged to use documentation, forums, and AI tools to problem-solve. For administrative issues, contact the support email.",
    "Can I put this internship on my resume or LinkedIn?": 
        "Absolutely! You should list it under your experience section and add the certificate to your LinkedIn profile once completed.",
    "Do I need to create a separate GitHub repo for each task?": 
        "You can either create one main repository with well-named subfolders for each task, or separate repositories. Just ensure the links provided in your submission form are accurate."
}

faq_questions = list(FAQ_DATA.keys())
faq_answers = list(FAQ_DATA.values())

# ==========================================
# STEP 2 & 3: NLP Processing & Intent Matching
# ==========================================
def preprocess(text):
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    cleaned_tokens = [word for word in tokens if word not in string.punctuation and word not in stop_words]
    return " ".join(cleaned_tokens)

preprocessed_faq_questions = [preprocess(q) for q in faq_questions]

def get_best_response(user_query):
    cleaned_query = preprocess(user_query)
    all_documents = preprocessed_faq_questions + [cleaned_query]
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_documents)
    
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    best_match_idx = similarity_scores.argmax()
    highest_score = similarity_scores[best_match_idx]
    
    if highest_score > 0.20:
        return faq_answers[best_match_idx]
    else:
        return "I couldn't find an exact match for that in my database. Could you try rephrasing your question regarding the internship?"

# ==========================================
# STEP 4: Integrated Drift UI Layout
# ==========================================
class AdvancedChatbotUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Configuration (Sleek Portrait Mobile Widget Style)
        self.title("CodeAlpha Support Widget")
        self.geometry("400x620")
        self.resizable(False, False)
        
        # Drift Palette Extraction
        ctk.set_appearance_mode("Light")
        self.bg_color = "#ffffff"       # Base canvas color
        self.purple_theme = "#b05cd6"   # Primary header/user bubble purple
        self.bot_bubble_bg = "#f0f2f5"  # Soft light-gray bot bubble
        self.text_dark = "#222222"      # High contrast dark gray reading text
        
        self.configure(fg_color=self.bg_color)
        self.create_widgets()
        
        # Initial System Greeting
        self.display_message("System", "Hello! Nice to meet you. Ask me any questions regarding your CodeAlpha virtual internship framework.")

    def create_widgets(self):
        # --- Top Header Frame ---
        header_frame = ctk.CTkFrame(self, fg_color=self.purple_theme, corner_radius=0, height=75)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        # Header Left: Meta Info (Vertical Stack)
        meta_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        meta_frame.pack(side="left", padx=18, pady=12)
        
        bot_name = ctk.CTkLabel(meta_frame, text="Assistant", font=("Segoe UI", 15, "bold"), text_color="#ffffff")
        bot_name.pack(anchor="w")
        
        status_label = ctk.CTkLabel(meta_frame, text="● Online Now", font=("Segoe UI", 11), text_color="#e1ffeb")
        status_label.pack(anchor="w", pady=(2, 0))
        
        # Header Right: Action Options Layout Facsimile
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right", padx=18)
        
        dots_label = ctk.CTkLabel(actions_frame, text="•••   ✕", font=("Segoe UI", 14, "bold"), text_color="#ffffff", cursor="hand2")
        dots_label.pack()

        # --- Main Chat Timeline Frame ---
        self.chat_history = ctk.CTkScrollableFrame(
            self, 
            fg_color=self.bg_color, 
            corner_radius=0,
            scrollbar_button_color="#dddddd",
            scrollbar_button_hover_color="#bbbbbb"
        )
        self.chat_history.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Thin Decorative Divider Line before Input Room
        divider = ctk.CTkFrame(self, fg_color="#f0f0f2", height=1)
        divider.pack(fill="x")
        
        # --- Bottom Input Deck Frame ---
        input_deck = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=0, height=75)
        input_deck.pack(fill="x", side="bottom")
        input_deck.pack_propagate(False)
        
        # Container to align Entry Field and Send Button side-by-side
        input_row = ctk.CTkFrame(input_deck, fg_color="transparent")
        input_row.pack(fill="x", padx=18, pady=(8, 0))
        
        # Text Input Field Bar
        self.entry_field = ctk.CTkEntry(
            input_row, 
            placeholder_text="Reply to Assistant...", 
            height=38,
            fg_color=self.bg_color,
            text_color=self.text_dark,
            border_width=0, 
            font=("Segoe UI", 13)
        )
        self.entry_field.pack(side="left", fill="x", expand=True)
        self.entry_field.bind("<Return>", lambda event: self.handle_send())
        
        # Modern Integrated Send Button
        send_button = ctk.CTkButton(
            input_row,
            text="➔",
            width=35,
            height=38,
            fg_color="transparent",
            text_color=self.purple_theme,
            hover_color=self.bot_bubble_bg,
            font=("Segoe UI", 16, "bold"),
            cursor="hand2",
            command=self.handle_send
        )
        send_button.pack(side="right", padx=(5, 0))
        
        # Mini Branding Row Alignment Anchor
        branding_row = ctk.CTkFrame(input_deck, fg_color="transparent")
        branding_row.pack(fill="x", padx=18, pady=(2, 4))
        
        drift_lbl = ctk.CTkLabel(branding_row, text="⚡ Powered by Drift", font=("Segoe UI", 10), text_color="#b2b2b6")
        drift_lbl.pack(side="right")

    def handle_send(self):
        user_text = self.entry_field.get().strip()
        if not user_text:
            return
            
        self.display_message("You", user_text)
        self.entry_field.delete(0, "end")
        
        # Smooth transactional delay matching typical chat interaction
        self.after(450, lambda: self.process_bot_response(user_text))

    def process_bot_response(self, user_text):
        bot_response = get_best_response(user_text)
        self.display_message("System", bot_response)

    def display_message(self, sender, text):
        is_user = (sender == "You")
        
        # Outer structural sequence row
        container = ctk.CTkFrame(self.chat_history, fg_color="transparent")
        container.pack(fill="x", pady=6, padx=12)
        
        if not is_user:
            # Bot label header stack element matching image logic
            sender_label = ctk.CTkLabel(
                container, 
                text="Assistant", 
                font=("Segoe UI", 10, "bold"), 
                text_color="#9c9ca2"
            )
            sender_label.pack(anchor="w", padx=6, pady=(0, 2))
            
            # Bot text capsule layout setup
            bubble = ctk.CTkFrame(container, fg_color=self.bot_bubble_bg, corner_radius=16)
            bubble.pack(side="left")
            
            text_color = self.text_dark
            align_anchor = "w"
        else:
            # User text capsule layout setup
            bubble = ctk.CTkFrame(container, fg_color=self.purple_theme, corner_radius=16)
            bubble.pack(side="right")
            
            text_color = "#ffffff"
            align_anchor = "e"
            
        # Interior label computing message wrap bounds cleanly
        text_label = ctk.CTkLabel(
            bubble, 
            text=text, 
            justify="left", 
            wraplength=250, 
            font=("Segoe UI", 13),
            text_color=text_color
        )
        text_label.pack(padx=14, pady=10, anchor=align_anchor)
        
        # Keep viewport dynamically locked to historical tail line
        self.chat_history._parent_canvas.yview_moveto(1.0)

if __name__ == "__main__":
    app = AdvancedChatbotUI()
    app.mainloop()