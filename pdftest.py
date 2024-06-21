from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Sustainability Report 2025', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

pdf = PDF()
pdf.add_page()

content = [
    ("Environmental Impact", "CO2 Emissions: 1800 tonnes per year\nNOX Emissions: 250 tonnes per year\nTotal Electric Vehicles: 75"),
    ("Climate Impact", "The company's operations significantly affect climate change, particularly through its production\nprocesses which release CO2 and NOX gases."),
    ("Potential Risks and Benefits", "Climate Risks: Significant risks due to climate change impacts, including regulatory challenges and\npotential damage to corporate reputation.\nClimate Opportunities: Financial benefits from climate-related activities, including cost reductions\nthrough energy efficiency and new market possibilities."),
    ("Corporate Strategy and Initiatives", "Business Strategy: The company's strategy is geared towards a sustainable economy. This involves\ninvestment in green energy and sustainable materials.\nSustainability Initiatives: Resources dedicated to addressing critical sustainability issues, including a\nspecialized sustainability team and collaborations with environmental organizations."),
    ("Policies and Goals", "Implemented Policies: Policies in place to manage critical sustainability issues, such as emission\nreduction, waste management, and water conservation.\nSustainability Goals: The company's targets include cutting CO2 emissions by 60% by 2035 and\nachieving net-zero emissions by 2045.")
]

for title, body in content:
    pdf.chapter_title(title)
    pdf.chapter_body(body)

pdf.output('Sustainability_Report_2025.pdf')
