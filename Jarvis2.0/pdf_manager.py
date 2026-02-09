from PyPDF2 import PdfReader, PdfWriter

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def list_form_fields(path):
    reader = PdfReader(path)
    fields = reader.get_fields()
    if not fields:
        return "No form fields found."
    return list(fields.keys())


def fill_pdf_form(input_path, output_path, fields: dict):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    writer.append_pages_from_reader(reader)

    # Update fields
    writer.update_page_form_field_values(
        writer.pages[0],
        fields
    )

    with open(output_path, "wb") as f:
        writer.write(f)

    return f"PDF saved to {output_path}"