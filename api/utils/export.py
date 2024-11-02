import pandas as pd
from fpdf import FPDF

def export_to_excel(queried_pages, broken_links, requires_access, file_path, search_type):
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        if search_type == "search_term" and queried_pages:
            search_df = pd.DataFrame(queried_pages, columns=["Search Term", "Found URL"])
            search_df.to_excel(writer, sheet_name="Search Results", index=False)
            adjust_column_width(search_df, writer, "Search Results")

        if search_type == "search_term":
            broken_df = pd.DataFrame(broken_links, columns=["Broken Link"])
        else:
            broken_df = pd.DataFrame(broken_links, columns=["Broken Link", "Origin Page URL"])
        broken_df.to_excel(writer, sheet_name="Broken Links", index=False)
        adjust_column_width(broken_df, writer, "Broken Links")

        access_df = pd.DataFrame(requires_access, columns=["Access Required Link"])
        access_df.to_excel(writer, sheet_name="Access Required Links", index=False)
        adjust_column_width(access_df, writer, "Access Required Links")

    print(f"Excel file saved to {file_path}")

def adjust_column_width(df, writer, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df):
        max_length = max(df[col].astype(str).map(len).max(), len(col))
        worksheet.set_column(idx, idx, max_length + 2)

def export_to_pdf(queried_pages, broken_links, requires_access, file_path, search_type):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Times", "B", 16)

    if search_type == "search_term" and queried_pages:
        pdf.cell(190, 10, "Scrape Results", ln=True, align="C")
        add_search_term_section(pdf, queried_pages)
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 16)
    pdf.cell(190, 10, "Broken Links", ln=True, align="C")
    if (broken_links):
        if search_type == "search_term":
            add_single_column_broken_links(pdf, broken_links)
        else:
            add_two_column_broken_links(pdf, broken_links)
    else:
        pdf.set_font("Times", "", 12)
        pdf.cell(190, 10, "No broken links reached.", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Times", "B", 16)
    pdf.cell(190, 10, "Access Required Links", ln=True, align="C")
    add_access_required_section(pdf, requires_access)

    pdf.output(file_path)
    print(f"PDF file saved to {file_path}")

def add_search_term_section(pdf, queried_pages):
    pdf.set_font("Times", "B", 12)
    pdf.cell(30, 10, "Matched String", 1, 0, "C")
    pdf.cell(160, 10, "Found URL", 1, 1, "C")
    pdf.set_font("Times", "", 12)

    for search_term, url in queried_pages:
        display_url = shorten_url(url)
        pdf.cell(30, 10, search_term, 1, 0, "C")
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("", "U")
        y_position = pdf.get_y()
        pdf.cell(160, 10, display_url, 1, 1)
        pdf.link(40, y_position, 160, 10, url)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Times", "", 12)

def add_single_column_broken_links(pdf, broken_links):
    pdf.set_font("Times", "", 12)
    pdf.set_text_color(0, 0, 255)
    pdf.set_font("", "U")
    for idx, broken in enumerate(broken_links):
        shortened_link = shorten_url(broken)
        pdf.multi_cell(190, 10, f"{idx + 1}. {shortened_link}", 1)
        y = pdf.get_y() - 10
        x = pdf.get_x() - 190
        pdf.link(x, y, 190, 10, broken)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", "", 12)

def add_two_column_broken_links(pdf, broken_links):
    pdf.set_font("Times", "B", 12)
    pdf.cell(95, 10, "Broken Link", 1, 0, "C")
    pdf.cell(95, 10, "Origin Page URL", 1, 1, "C")
    pdf.set_font("Times", "", 12)

    for broken, origin in broken_links:
        broken_display = shorten_url(broken, max_length=48)
        origin_display = shorten_url(origin, max_length=48)
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("", "U")
        pdf.cell(95, 10, broken_display, 1, 0)
        y_broken = pdf.get_y()
        pdf.link(10, y_broken, 95, 10, broken)
        pdf.cell(95, 10, origin_display, 1, 1)
        y_origin = pdf.get_y()
        pdf.link(105, y_origin, 95, 10, origin)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Times", "", 12)

def add_access_required_section(pdf, requires_access):
    pdf.set_font("Times", "", 12)
    if requires_access:
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("", "U")
        for idx, access in enumerate(requires_access):
            access_display = shorten_url(access, max_length=170)
            pdf.multi_cell(190, 10, f"{idx + 1}. {access_display}", 1)
            y = pdf.get_y() - 10
            pdf.link(pdf.get_x() - 190, y, 190, 10, access)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Times", "", 12)
    else:
        pdf.cell(190, 10, "No access-required links reached.", ln=True, align="C")

def shorten_url(url, max_length=75):
    return url if len(url) <= max_length else url[: max_length - 3] + "..."

class PDF(FPDF):
    def header(self):
        self.set_font("Times", "I", 12)
        self.set_text_color(0, 0, 0)
        self.set_xy(180, 5)
        self.cell(0, 10, "Search Results", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "I", 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")
