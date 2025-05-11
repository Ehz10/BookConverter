from flask import Flask, request, send_file, render_template
import os
import uuid
import fitz  # PyMuPDF
from ebooklib import epub

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'pdf' not in request.files:
        return "No file uploaded", 400

    file = request.files['pdf']
    if file.filename == '':
        return "No selected file", 400

    # Get original name and create safe temp name for upload
    original_filename = file.filename
    base_name = os.path.splitext(original_filename)[0]
    temp_filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
    file.save(filepath)

    # Output EPUB path with original name
    epub_path = os.path.join(UPLOAD_FOLDER, f"{base_name}.epub")

    try:
        # Open PDF
        doc = fitz.open(filepath)

        # Create EPUB
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(base_name)
        book.set_language('en')

        chapters = []
        for i, page in enumerate(doc):
            text = page.get_text()
            formatted_text = text.replace("\n", "<br>")
            chapter = epub.EpubHtml(
                title=f'Page {i+1}', file_name=f'page_{i+1}.xhtml', lang='en'
            )
            chapter.content = f'<h1>Page {i+1}</h1><p>{formatted_text}</p>'
            book.add_item(chapter)
            chapters.append(chapter)

        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav'] + chapters

        epub.write_epub(epub_path, book)
        doc.close()

        return send_file(epub_path, as_attachment=True, download_name=f"{base_name}.epub")

    except Exception as e:
        return f"Conversion failed: {e}", 500

    finally:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

if __name__ == '__main__':
    app.run(debug=True)
