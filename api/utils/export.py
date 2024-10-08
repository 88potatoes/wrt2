import pandas as pd
from fpdf import FPDF


def export_to_excel(queried_pages, requires_access, broken_links, file_path, search_type):
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        if search_type == "search_term":
            search_df = pd.DataFrame(queried_pages, columns=["Search Term", "Found URL"])
        broken_df = pd.DataFrame(broken_links, columns=["Broken Link"])
        access_df = pd.DataFrame(requires_access, columns=["Access Required Link"])

        # Write dataframes to Excel
        if search_type == "search_term":
            search_df.to_excel(writer, sheet_name="Search Results", index=False)
        broken_df.to_excel(writer, sheet_name="Broken Links", index=False)
        access_df.to_excel(writer, sheet_name="Access Required Links", index=False)

        # Get the xlsxwriter workbook and worksheet objects
        # workbook = writer.book

        # Adjust column widths for 'Search Results' sheet
        if search_type == "search_term":
            search_worksheet = writer.sheets["Search Results"]
            for idx, col in enumerate(search_df):
                max_length = max(search_df[col].astype(str).map(len).max(), len(col))
                search_worksheet.set_column(idx, idx, max_length + 2)

        # Adjust column widths for 'Broken Links' sheet
        broken_worksheet = writer.sheets["Broken Links"]
        for idx, col in enumerate(broken_df):
            max_length = max(broken_df[col].astype(str).map(len).max(), len(col))
            broken_worksheet.set_column(idx, idx, max_length + 2)

        # Adjust column widths for 'Access Required Links' sheet
        access_worksheet = writer.sheets["Access Required Links"]
        for idx, col in enumerate(access_df):
            max_length = max(access_df[col].astype(str).map(len).max(), len(col))
            access_worksheet.set_column(idx, idx, max_length + 2)

    print(f"Excel file saved to {file_path}")


def shorten_url(url, max_length=75):
    """Shortens the URL for display purposes to a single length."""
    if len(url) <= max_length:
        return url
    else:
        return url[: max_length - 3] + "..."


def export_to_pdf(queried_pages, requires_access, broken_links, file_path, search_type):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Times", "B", 16)

    if search_type == "search_term":
        pdf.cell(190, 10, "Scrape Results", ln=True, align="C")

        if queried_pages:
            # Set up column headers for the Search Results
            pdf.set_font("Times", "B", 12)
            pdf.cell(30, 10, "Matched String", 1, 0, "C")  # Cell width: 30
            pdf.cell(160, 10, "Found URL", 1, 1, "C")  # Cell width: 160

            # Add data for Search Results (with wrapping text)
            pdf.set_font("Times", "", 12)
            for page in queried_pages:
                search_term = page[0]
                url = page[1]

                # Shorten the URL for display
                display_url = shorten_url(url)

                # Print the search term and shortened URL on the same line
                pdf.cell(30, 10, search_term, 1, 0, "C")  # Cell for the search term

                # Set text color and style for the URL
                pdf.set_text_color(0, 0, 255)
                pdf.set_font("", "U")  # Underline for the URL

                # Get current Y position for link overlay
                y_after_url = pdf.get_y()

                # Add the shortened URL and create clickable link overlay
                pdf.cell(160, 10, display_url, 1, 1)  # Show the shortened URL
                pdf.link(40, y_after_url, 160, 10, url)  # Add clickable link overlay

                # Reset text color and font
                pdf.set_text_color(0, 0, 0)  # Reset text color to black
                pdf.set_font("Times", "", 12)  # Reset text to not be underlined
        else:
            pdf.set_font("Times", "", 12)
            pdf.cell(190, 10, "No search results found.", ln=True, align="C")

    # Add Broken Links table
    pdf.ln(10)  # Add space before new section
    pdf.set_font("Times", "B", 16)
    pdf.cell(190, 10, "Broken Links", ln=True, align="C")

    pdf.set_font("Times", "", 12)
    if broken_links:
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("", "U")  # Underline

        for idx, broken in enumerate(broken_links):
            shortened_link = shorten_url(broken)
            # Set text color to blue and underline for the clickable link
            pdf.multi_cell(
                190, 10, f"{idx + 1}. {shortened_link}", 1
            )  # Use multi_cell for wrapping
            y = pdf.get_y() - 10  # Adjust for the height of the cell
            x = pdf.get_x() - 190  # Adjust for the width of the cell
            pdf.link(x, y, 190, 10, broken)  # Add clickable link overlay

        pdf.set_text_color(0, 0, 0)  # Reset text color to black
        pdf.set_font("Times", "", 12)  # Reset text to not be underlined
    else:
        pdf.cell(190, 10, "No broken links reached.", ln=True, align="C")

    # Add Access Required Links table
    pdf.ln(10)  # Add space before new section
    pdf.set_font("Times", "B", 16)
    pdf.cell(190, 10, "Access Required Links", ln=True, align="C")

    pdf.set_font("Times", "", 12)
    if requires_access:
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("", "U")  # Underline

        for idx, access in enumerate(requires_access):
            shortened_link = shorten_url(access)
            # Set text color to blue and underline for the clickable link
            pdf.multi_cell(
                190, 10, f"{idx + 1}. {shortened_link}", 1
            )  # Use multi_cell for wrapping
            y = pdf.get_y() - 10  # Adjust for the height of the cell
            x = pdf.get_x() - 190  # Adjust for the width of the cell
            pdf.link(x, y, 190, 10, access)  # Add clickable link overlay

        pdf.set_text_color(0, 0, 0)  # Reset text color to black
        pdf.set_font("Times", "", 12)  # Reset text to not be underlined
    else:
        pdf.cell(190, 10, "No access-required links reached.", ln=True, align="C")

    # Save PDF to file path
    pdf.output(file_path)

    print(f"PDF file saved to {file_path}")


class PDF(FPDF):
    def header(self):
        # Set font for header
        self.set_font("Times", "I", 12)
        # Set text color to black
        self.set_text_color(0, 0, 0)
        # Set position for header
        self.set_xy(180, 5)
        # Title
        self.cell(0, 10, "Search Results", 0, 1, "C")

    def footer(self):
        # Move to 1.5 cm from bottom
        self.set_y(-15)
        # Set font for footer
        self.set_font("Times", "I", 8)
        # Set text color to black
        self.set_text_color(0, 0, 0)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")
