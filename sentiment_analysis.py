import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from threading import Thread
import pandas as pd
from textblob import TextBlob
from googleapiclient.discovery import build
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Define your YouTube API key
api_key = "AIzaSyDBnMcES66SjJDBHfc6ZcDN42EcfjL_6EE"

# Load the list of profanity words from an external file
with open(r"C:\Users\Vaibhav\OneDrive\Desktop\Rushi\YOUTUBE_ANALYSIS\profanity_words.txt", "r") as file:
    profanity_words = [word.strip() for word in file.readlines()]

# Function to retrieve video comments from a YouTube video
def get_video_comments(api_key, video_url):
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_id = video_url.split("v=")[1]

    comments = []
    nextPageToken = None

    while True:
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            pageToken=nextPageToken
        ).execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            # Clean comments by removing emojis and non-alphanumeric characters
            comment = clean_comment(comment)
            comments.append(comment)

        nextPageToken = response.get('nextPageToken')

        if not nextPageToken:
            break

    return comments

# Function to clean comments by removing emojis and non-alphanumeric characters
def clean_comment(comment):
    # Remove emojis
    comment = comment.encode('ascii', 'ignore').decode('ascii')
    # Remove non-alphanumeric characters except spaces
    comment = re.sub(r'[^a-zA-Z0-9\s]', '', comment)
    return comment

# Function to analyze sentiment and profanity in comments
def analyze_comments(comments):
    data = {'Comment': comments, 'Polarity': [], 'Sentiment Category': [], 'Vulgar': []}

    for comment in comments:
        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity
        data['Polarity'].append(polarity)

        # Categorize comments based on sentiment polarity
        if polarity > 0.1:
            sentiment_category = 'Positive'
        elif polarity < -0.1:
            sentiment_category = 'Negative'
        else:
            sentiment_category = 'Neutral'

        data['Sentiment Category'].append(sentiment_category)

        # Check for profanity
        is_vulgar = is_profane(comment)
        data['Vulgar'].append(is_vulgar)

    return pd.DataFrame(data)

# Function to check if a comment contains profanity
def is_profane(comment):
    # Check against the list of profanity words
    for word in profanity_words:
        if word.lower() in comment.lower():
            return True
    return False

# Main application class
class SentimentAnalysisApp:
    def __init__(self, master):
        self.master = master
        self.master.title("YouTube Sentiment Analysis")

        # Create a notebook to manage tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill='both', expand=True)

        # Create tabs
        self.analysis_tab = ttk.Frame(self.notebook)
        self.pie_chart_tab = ttk.Frame(self.notebook)
        self.bar_chart_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.analysis_tab, text='Analysis')
        self.notebook.add(self.pie_chart_tab, text='Pie Chart')
        self.notebook.add(self.bar_chart_tab, text='Bar Chart')

        # Analysis tab
        self.label = ttk.Label(self.analysis_tab, text="Enter YouTube video URL:")
        self.label.pack(pady=10)

        self.url_entry = ttk.Entry(self.analysis_tab, width=50)
        self.url_entry.pack(pady=10)

        self.analyze_button = ttk.Button(self.analysis_tab, text="Analyze Comments", command=self.analyze_comments)
        self.analyze_button.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(self.analysis_tab, width=80, height=20)
        self.result_text.pack(pady=10)

        self.table_frame = ttk.Frame(self.analysis_tab)
        self.table_frame.pack(pady=10)

        # Create a table to display the results
        self.result_table = ttk.Treeview(self.table_frame)
        self.result_table["columns"] = ("Comment", "Polarity", "Sentiment Category", "Vulgar")  # Column names

        for column in self.result_table["columns"]:
            self.result_table.column(column, anchor=tk.W, width=150)  # Adjusted column width
            self.result_table.heading(column, text=column, anchor=tk.W)

        self.result_table.pack()

        self.progress_label = ttk.Label(self.analysis_tab, text="")
        self.progress_label.pack(pady=10)

        # Pie Chart tab
        self.pie_chart_frame = ttk.Frame(self.pie_chart_tab)
        self.pie_chart_frame.pack(pady=10)

        # Bar Chart tab
        self.bar_chart_frame = ttk.Frame(self.bar_chart_tab)
        self.bar_chart_frame.pack(pady=10)

    def update_progress(self, message):
        self.progress_label['text'] = message

    def update_table(self, output_table):
        # Clear existing items in the table
        for item in self.result_table.get_children():
            self.result_table.delete(item)

        # Insert new values into the table
        for index, row in output_table.iterrows():
            values = (row['Comment'], row['Polarity'], row['Sentiment Category'], row['Vulgar'])
            self.result_table.insert("", "end", values=values)

    def create_pie_chart(self, output_table):
        labels = ['Positive', 'Negative', 'Neutral', 'Vulgar']
        sizes = [output_table['Sentiment Category'].value_counts().get(label, 0) for label in labels]

        # Increase the size of the figure
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plot the pie chart
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)

        # Set the aspect ratio to be equal, ensuring the pie is drawn as a circle.
        ax.axis('equal')

        # Create a Tkinter canvas widget and embed the Matplotlib figure in it
        canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
        canvas_widget = canvas.get_tk_widget()

        # Pack the canvas widget into the Tkinter window
        canvas_widget.pack()

        # Display the Matplotlib figure within the Tkinter window
        canvas.draw()

    def create_bar_chart(self, output_table):
        sentiment_counts = output_table['Sentiment Category'].value_counts()
        vulgar_count = output_table['Vulgar'].sum()

        labels = list(sentiment_counts.index) + ['Vulgar']
        counts = list(sentiment_counts.values) + [vulgar_count]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(labels, counts)

        ax.set_xlabel('Category')
        ax.set_ylabel('Number of Comments')
        ax.set_title('Number of Comments by Category')

        canvas = FigureCanvasTkAgg(fig, master=self.bar_chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack()
        canvas.draw()

    def analyze_comments(self):
        video_url = self.url_entry.get()
        if not video_url:
            messagebox.showinfo("Error", "Please enter a valid YouTube video URL.")
            return

        # Disable the analyze button during analysis
        self.analyze_button['state'] = 'disabled'
        self.update_progress("Analyzing comments...")

        # Run the analysis in a separate thread to keep the GUI responsive
        thread = Thread(target=self.run_analysis, args=(video_url,))
        thread.start()

    def run_analysis(self, video_url):
        try:
            comments = get_video_comments(api_key, video_url)

            if len(comments) == 0:
                result = "No comments found for the given video."
            else:
                output_table = analyze_comments(comments)

                result = "Sentiment Analysis Results:\n" + str(output_table)

                # Update the result_text in the main thread
                self.master.after(0, lambda: self.result_text.delete(1.0, tk.END))
                self.master.after(0, lambda: self.result_text.insert(tk.END, result + "\n"))

                # Update the table
                self.update_table(output_table)

                # Create and display the pie chart
                self.create_pie_chart(output_table)

                # Create and display the bar chart
                self.create_bar_chart(output_table)

        except Exception as e:
            result = f"An error occurred: {str(e)}"
            # Update the result_text in the main thread
            self.master.after(0, lambda: self.result_text.delete(1.0, tk.END))
            self.master.after(0, lambda: self.result_text.insert(tk.END, result + "\n"))

        finally:
            # Enable the analyze button after analysis is complete
            self.master.after(0, self.enable_analyze_button)

    def enable_analyze_button(self):
        self.analyze_button['state'] = 'normal'
        self.update_progress("Analysis complete.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SentimentAnalysisApp(root)
    root.mainloop()
