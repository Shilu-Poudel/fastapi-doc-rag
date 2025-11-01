from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', size=12)

with open('sample_content.txt', 'r') as f:
    content = f.read()
    
pdf.multi_cell(0, 10, txt=content)
pdf.output('ai_overview.pdf')