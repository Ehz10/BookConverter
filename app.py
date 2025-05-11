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

    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    epub_path = filepath.replace('.pdf', '.epub')

    try:
        # Open the PDF
        doc = fitz.open(filepath)

        # Create EPUB book
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title('Converted PDF')
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

        return send_file(epub_path, as_attachment=True)

    except Exception as e:
        return f"Conversion failed: {e}", 500

    finally:
        # Clean up uploaded file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

if __name__ == '__main__':
    app.run(debug=True)