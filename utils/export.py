import pandas as pd
from fpdf import FPDF

# Function to export search results to Excel
def export_to_excel(queried_pages, requires_access, broken_links, file_path):
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        search_df = pd.DataFrame(queried_pages, columns=['Search Term', 'Found URL'])
        broken_df = pd.DataFrame(broken_links, columns=['Broken Link'])
        access_df = pd.DataFrame(requires_access, columns=['Access Required Link'])

        # Write dataframes to Excel
        search_df.to_excel(writer, sheet_name='Search Results', index=False)
        broken_df.to_excel(writer, sheet_name='Broken Links', index=False)
        access_df.to_excel(writer, sheet_name='Access Required Links', index=False)

    print(f"Excel file saved to {file_path}")

def export_to_pdf(queried_pages, requires_access, broken_links, file_path):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Times', 'B', 16)

    pdf.cell(190, 10, 'Scrape Results', ln=True, align='C')

    # Set up column headers for the Search Results
    pdf.set_font('Times', 'B', 12)
    pdf.cell(30, 10, 'Search Term', 1, 0, 'C')  # Cell width: 30
    pdf.cell(160, 10, 'Found URL', 1, 1, 'C')  # Cell width: 160

    # Add data for Search Results (with wrapping text)
    pdf.set_font('Times', '', 12)

    # Helper function to calculate the number of lines a multi_cell() will take
    def multi_cell_height(text, width, line_height):
        num_lines = pdf.get_string_width(text) // width
        return (num_lines + 1) * line_height
    
    for page in queried_pages:
        search_term = page[0]
        url = page[1]

        y_before_url = pdf.get_y()
        url_height = multi_cell_height(url, 160, 10)
        search_term_height = max(10, url_height)

        # Search Term column with wrapping text
        pdf.multi_cell(30, search_term_height, search_term, 1, 'C')

        # Move cursor back to the right for the URL column
        pdf.set_xy(40, y_before_url)

        # URL column with wrapping text
        pdf.multi_cell(160, 10, url, 1)

    # Add Broken Links table
    pdf.ln(10)  # Add space before new section
    pdf.set_font('Times', 'B', 16)
    pdf.cell(190, 10, 'Broken Links', ln=True, align='C')

    pdf.set_font('Times', '', 12)
    for idx, broken in enumerate(broken_links):
        pdf.cell(190, 10, f'{idx + 1}. {broken}', 1, ln=True)

    # Add Access Required Links table
    pdf.ln(10)  # Add space before new section
    pdf.set_font('Times', 'B', 16)
    pdf.cell(190, 10, 'Access Required Links', ln=True, align='C')

    pdf.set_font('Times', '', 12)
    for idx, access in enumerate(requires_access):
        pdf.cell(190, 10, f'{idx + 1}. {access}', 1, ln=True)

    # Save PDF to file path
    pdf.output(file_path)

    print(f"PDF file saved to {file_path}")

class PDF(FPDF):
    def header(self):
        # Set font for header
        self.set_font('Times', '', 12)
        # Set position for header
        self.set_xy(180, 5)
        # Title
        self.cell(0, 10, 'Search Results', 0, 1, 'C')

    def footer(self):
        # Move to 1.5 cm from bottom
        self.set_y(-15)
        # Set font for footer
        self.set_font('Times', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')