# --- ELEGANCKI PDF ---
            try:
                from fpdf import FPDF

                class ElegantPDF(FPDF):
                    def header(self):
                        # Pasek dekoracyjny na górze
                        self.set_fill_color(211, 47, 47)  # Kolor czerwony (z Twojego Excela)
                        self.rect(0, 0, 297, 20, 'F') 
                        
                        if hasattr(self, 'font_ready') and self.font_ready:
                            self.set_font('Roboto', '', 16)
                        else:
                            self.set_font('helvetica', 'B', 16)
                            
                        self.set_text_color(255, 255, 255)
                        tytul = f"Raport Wydatków - wygenerowano dnia {datetime.now().strftime('%d.%m.%Y')}"
                        self.cell(0, 10, self.clean_text(tytul), ln=True, align='C')
                        self.ln(10)

                    def footer(self):
                        self.set_y(-15)
                        if hasattr(self, 'font_ready') and self.font_ready:
                            self.set_font('Roboto', '', 8)
                        else:
                            self.set_font('helvetica', 'I', 8)
                        self.set_text_color(128, 128, 128)
                        self.cell(0, 10, f'Strona {self.page_no()} / {{nb}}', align='C')

                    def clean_text(self, tekst):
                        t = str(tekst).replace('✅', '').strip()
                        if not hasattr(self, 'font_ready') or not self.font_ready:
                            zamienniki = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z',
                                          'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z'}
                            for pl, asc in zamienniki.items():
                                t = t.replace(pl, asc)
                        return t

                # Przygotowanie czcionek
                font_path = "Roboto-Regular.ttf"
                font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto-Regular.ttf"
                if not os.path.exists(font_path):
                    try: urllib.request.urlretrieve(font_url, font_path)
                    except: pass

                pdf = ElegantPDF(orientation='L', unit='mm', format='A4')
                pdf.alias_nb_pages()
                
                # Konfiguracja czcionki polskiej
                if os.path.exists(font_path):
                    pdf.add_font('Roboto', '', font_path, uni=True)
                    pdf.font_ready = True
                else:
                    pdf.font_ready = False

                pdf.add_page()
                
                # Nagłówki tabeli
                cols = [30, 65, 25, 45, 40, 45]
                headers = ["Data", "Sklep / Dostawca", "Kwota", "Status", "Metoda", "Użytkownik"]
                
                pdf.set_fill_color(60, 60, 60) # Ciemnoszary nagłówek tabeli
                pdf.set_text_color(255, 255, 255)
                if pdf.font_ready: pdf.set_font('Roboto', '', 10)
                else: pdf.set_font('helvetica', 'B', 10)

                for i, h in enumerate(headers):
                    pdf.cell(cols[i], 10, pdf.clean_text(h), border=0, ln=0, align='C', fill=True)
                pdf.ln()

                # Dane - Efekt Zebry
                pdf.set_text_color(0, 0, 0)
                if pdf.font_ready: pdf.set_font('Roboto', '', 9)
                else: pdf.set_font('helvetica', '', 9)
                
                fill = False
                for index, row in df_f.iterrows():
                    # Kolor tła dla co drugiego wiersza
                    if fill: pdf.set_fill_color(245, 245, 245)
                    else: pdf.set_fill_color(255, 255, 255)
                    
                    pdf.cell(cols[0], 9, pdf.clean_text(row['data_zakupu']), border='B', fill=True)
                    pdf.cell(cols[1], 9, pdf.clean_text(str(row['sklep'])[:40]), border='B', fill=True)
                    pdf.cell(cols[2], 9, pdf.clean_text(f"{row['kwota']:.2f} zł"), border='B', align='R', fill=True)
                    pdf.cell(cols[3], 9, pdf.clean_text(str(row['status'])[:20]), border='B', fill=True)
                    pdf.cell(cols[4], 9, pdf.clean_text(str(row['metoda_platnosci'])), border='B', fill=True)
                    pdf.cell(cols[5], 9, pdf.clean_text(str(row['zgloszone_przez'])), border='B', fill=True)
                    pdf.ln()
                    fill = not fill # Przełącz kolor

                pdf_output = pdf.output()
                c_ex2.download_button(
                    label="📄 Pobierz Elegancki PDF",
                    data=bytes(pdf_output),
                    file_name=f"raport_wydatkow_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                c_ex2.error(f"Błąd PDF: {e}")
