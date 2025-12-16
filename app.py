import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Smart Library System", page_icon="📚", layout="wide")
def add_bg_animation():
    st.markdown(
        """
        <style>
        /* 1. The Animated Gradient Background */
        .stApp {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }

        @keyframes gradient {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }

        /* 2. Make Text Readable (Glassmorphism Effect) */
        /* This targets the main content blocks to give them a white, see-through look */
        [data-testid="stSidebar"] {
            background-color: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(10px);
        }
        
        .stDataFrame, .stMetric, .stForm {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* 3. Customize Buttons */
        .stButton>button {
            color: white;
            background: #FF4B4B;
            border-radius: 20px;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            background: #FF0000;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- CALL THE FUNCTION ---
add_bg_animation()
# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            category TEXT,
            status TEXT,
            borrower TEXT,
            date_issued TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on first run
init_db()

# --- DATABASE FUNCTIONS ---
def add_book_to_db(book_id, title, author, category):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)', 
                  (book_id, title, author, category, 'Available', None, None))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # ID already exists
    finally:
        conn.close()

def get_all_books():
    conn = sqlite3.connect('library.db')
    df = pd.read_sql_query("SELECT * FROM books", conn)
    conn.close()
    return df

def update_status(book_id, status, borrower=None, date=None):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("UPDATE books SET status=?, borrower=?, date_issued=? WHERE book_id=?", 
              (status, borrower, date, book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Smart Library System", page_icon="📚", layout="wide")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📚 Library Menu")
menu = st.sidebar.radio("Go to:", ["Dashboard", "Add New Book", "Issue Book", "Return Book", "Search & Manage"])

# --- PAGE 1: DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Library Dashboard")
    df = get_all_books()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        total_books = len(df)
        issued_books = len(df[df['status'] == 'Issued'])
        available_books = total_books - issued_books
        
        col1.metric("Total Books", total_books)
        col2.metric("Books Issued", issued_books, delta_color="inverse")
        col3.metric("Available Now", available_books)
        
        st.markdown("### Recently Added Books")
        st.dataframe(df.tail(5))
    else:
        st.info("Library is empty. Go to 'Add New Book' to start.")

# --- PAGE 2: ADD BOOK ---
elif menu == "Add New Book":
    st.title("➕ Add New Book")
    with st.form("add_book_form"):
        c1, c2 = st.columns(2)
        b_id = c1.text_input("Book ID (Unique)", placeholder="e.g., BK001")
        b_cat = c2.selectbox("Category", ["Engineering", "Fiction", "Science", "History", "Business"])
        b_title = st.text_input("Book Title")
        b_author = st.text_input("Author Name")
        
        submitted = st.form_submit_button("Add Book")
        
        if submitted:
            if b_id and b_title:
                success = add_book_to_db(b_id, b_title, b_author, b_cat)
                if success:
                    st.success(f"✅ Book '{b_title}' added successfully!")
                else:
                    st.error("❌ Error: Book ID already exists.")
            else:
                st.warning("⚠️ Please fill in all fields.")

# --- PAGE 3: ISSUE BOOK ---
elif menu == "Issue Book":
    st.title("📤 Issue Book to Student")
    df = get_all_books()
    
    # Filter only available books
    available_books = df[df['status'] == 'Available']
    
    if available_books.empty:
        st.info("No books available to issue.")
    else:
        # Create a list of strings "ID - Title" for the dropdown
        book_options = available_books['book_id'] + " - " + available_books['title']
        selected_book = st.selectbox("Select Book to Issue", book_options)
        student_name = st.text_input("Student Name / USN")
        
        if st.button("Confirm Issue"):
            if student_name:
                # Extract Book ID from the selection string
                book_id_to_issue = selected_book.split(" - ")[0]
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                update_status(book_id_to_issue, 'Issued', student_name, date_now)
                st.success(f"✅ Book issued to {student_name}!")
                st.rerun() # Refresh page to update list
            else:
                st.error("Please enter Student Name.")

# --- PAGE 4: RETURN BOOK ---
elif menu == "Return Book":
    st.title("📥 Return Book")
    df = get_all_books()
    
    # Filter only issued books
    issued_books = df[df['status'] == 'Issued']
    
    if issued_books.empty:
        st.info("No books are currently issued out.")
    else:
        book_options = issued_books['book_id'] + " - " + issued_books['title'] + " (Borrowed by: " + issued_books['borrower'] + ")"
        selected_book = st.selectbox("Select Book to Return", book_options)
        
        if st.button("Process Return"):
            book_id_to_return = selected_book.split(" - ")[0]
            update_status(book_id_to_return, 'Available')
            st.success("✅ Book returned successfully!")
            st.rerun()

# --- PAGE 5: SEARCH & MANAGE ---
elif menu == "Search & Manage":
    st.title("🔍 Search & Manage Inventory")
    df = get_all_books()
    
    # Search Bar
    search_term = st.text_input("Search by Title, Author, or ID")
    
    if search_term:
        mask = df.apply(lambda x: x.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_display = df[mask]
    else:
        df_display = df
        
    st.dataframe(df_display, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🗑️ Delete Book")
    del_id = st.text_input("Enter Book ID to Delete")
    if st.button("Delete Permanently", type="primary"):
        if del_id in df['book_id'].values:
            delete_book(del_id)
            st.warning(f"Book {del_id} deleted.")
            st.rerun()
        else:
            st.error("Book ID not found.")