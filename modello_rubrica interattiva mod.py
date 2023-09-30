import sqlite3
import re
import operator
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import PhotoImage
from PIL import Image, ImageTk
import pyttsx3  # text-to-speech
import speech_recognition as sr
# Inizializza il riconoscitore vocale
recognizer = sr.Recognizer()
# In questo modo, la funzione recognize_speech() sarà chiamata all'interno di voice_input() ogni volta che è necessario ottenere l'input vocale. 
# Assicurati che recognizer sia stato inizializzato in precedenza nel tuo codice. Ricorda anche di gestire i casi in cui il riconoscimento vocale 
# non è riuscito a capire l'audio o se si è verificato un errore durante la richiesta al servizio di riconoscimento vocale.
campi = ["nome", "numero", "email", "indirizzo"]
indice_campo_attuale = 0
# Dichiarazione delle variabili globali per memorizzare il campo corrente e il testo riconosciuto
campo_corrente = None
testo_inserito = ["", "", "", ""]
def recognize_speech():
    with sr.Microphone() as source:
        print("Ascolto...")
        audio = recognizer.listen(source)
        try:
            # Trasforma l'audio in testo usando il riconoscimento vocale di Google
            testo = recognizer.recognize_google(audio, language="it-IT")
            print(f"Hai detto: {testo}")
            return testo
        except sr.UnknownValueError:
            print("Non ho capito l'audio.")
            return ""
        except sr.RequestError as e:
            print(f"Errore nella richiesta al servizio di riconoscimento vocale; {e}")
            return ""

def set_field(campo, testo):
    if campo == "nome":
        name_entry.insert(0, testo)
    elif campo == "numero":
        telephone_entry.insert(0, testo)
    elif campo == "email":
        email_entry.insert(0, testo)
    elif campo == "indirizzo":
        address_entry.insert(0, testo)

# def is_valid_email(email):
#     # Pattern regex per validare l'indirizzo email
#     pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
#     if re.match(pattern, email):
#         return True
#     else:
#         return False

def voice_input():
    global indice_campo_attuale
    global campo_corrente

    while indice_campo_attuale < len(campi):
        # Ottieni l'input vocale
        testo = recognize_speech()

        # Verifica se il testo è vuoto
        if testo:
            if campo_corrente == "nome" or campo_corrente == "indirizzo":
                # Sostituisci gli spazi con "-"
                testo_sostituito = testo.replace(" ", "-")
            else:
                # Rimuovi gli spazi tra le parole
                testo_sostituito = testo.replace(" ", "")
                
            if campo_corrente == "nome":
                # Assumi che il primo pezzo sia il nome e il resto sia il cognome
                parti_nome_cognome = testo_sostituito.split(maxsplit=1)
                if len(parti_nome_cognome) > 1:
                    nome, cognome = parti_nome_cognome
                else:
                    nome, cognome = parti_nome_cognome[0], ""  # Se non c'è cognome
                # Inserisci il nome nel campo nome
                set_field("nome", nome.strip())
                # Inserisci il cognome nel campo cognome
                set_field("cognome", cognome.strip())
            elif "chiocciola" in testo_sostituito.lower():
                email = testo_sostituito.replace("chiocciola", "@").lower()
                set_field(campi[indice_campo_attuale], email)
            elif "punto" in testo_sostituito.lower():
                email_con_punto = testo_sostituito.replace("punto", ".").lower()
                set_field(campi[indice_campo_attuale], email_con_punto)
            elif campo_corrente == "numero":
                # Rimuovi gli spazi dal numero di telefono
                numero_telefono = ''.join(filter(str.isdigit, testo_sostituito))
                set_field(campi[indice_campo_attuale], numero_telefono)
            else:
                # Altrimenti, inserisci il testo senza spazi nella lista nel campo corrente
                set_field(campi[indice_campo_attuale], testo_sostituito)

            indice_campo_attuale += 1

            # Se hai compilato tutti i campi, esci dal ciclo
            if indice_campo_attuale >= len(campi):
                break
        else:
            # Se il testo è vuoto, richiama nuovamente la funzione per ottenere un input vocale valido
            voice_input()

# ***** FUNCTIONS *****
def add_contact():
    # Extract data from entry fields
    name = name_entry.get()
    telephone = telephone_entry.get()
    email = email_entry.get()
    address = address_entry.get()
    if name and telephone and email and address:
        # Create a new dictionary for collecting contact information
        contact = {"Nome":name, "Telefono":telephone, "Email":email, "Indirizzo":address}
        # Add dictionary to the list 'rubrica'
        rubrica.append(contact)
        rubrica_session.append(contact)
        cursor.execute("INSERT INTO CONTATTI VALUES (?, ?, ?, ?)", (name, telephone, email, address))
        qta_numeri_label.config(text = f"{count_numbers()} contatti con numeri telefonici")
        conn.commit()
        print_contacts(rubrica_session, treeview_contacts)
        print_contacts(rubrica, treeview_save)
        # Clear fields
        name_entry.delete(0, tk.END)
        telephone_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        address_entry.delete(0, tk.END)
    else:
        tk.messagebox.showwarning("Errore", message = "Compilare tutti i campi obbligatori")

def count_numbers():
    result = cursor.execute("SELECT COUNT(*) FROM CONTATTI")
    return result.fetchone()[0]
    
def search_contact():
    treeview_sr.delete(*treeview_sr.get_children())
    searched_field = wanted_entry.get()
    contatti_cercati = []
    for contatto in rubrica:
        if(contatto["Nome"] == searched_field or contatto["Email"] == searched_field or
            contatto["Indirizzo"] == searched_field):
            contatti_cercati.append(contatto)
    print_contacts(contatti_cercati, treeview_sr)
    return contatti_cercati

def remove_contact():
    contatti_cercati = search_contact()
    if len(contatti_cercati) == 1:
        rubrica.remove(contatti_cercati[0])
        if contatti_cercati[0] in rubrica_session:
            rubrica_session.remove(contatti_cercati[0])
        cursor.execute("DELETE FROM CONTATTI WHERE name = ? AND telefono = ? AND email = ? AND address = ?",
                       (contatti_cercati[0]["Nome"], contatti_cercati[0]["Telefono"], 
                        contatti_cercati[0]["Email"], contatti_cercati[0]["Indirizzo"]))
        conn.commit()
    else:   # more than one contacts corresponds to the research
        treeview_sr.bind("<<TreeViewSelect>>", lambda event: remove_selected_item(event))
    qta_numeri_label.config(text = f"{count_numbers()} contatti con numeri telefonici")
    print_contacts(rubrica, treeview_save)
    wanted_entry.delete(0, tk.END)
    treeview_sr.delete(*treeview_sr.get_children())

def remove_selected_item(event):
    selected_contact = treeview_sr.selection()[0]  # ('I001',)
    print("ciao")
    # treeview_save.delete(selected_contact)
    print(treeview_sr.item(selected_contact, "values"))

def print_contacts(lista_contatti: list, treeview: ttk.Treeview):
    treeview.delete(*treeview.get_children())
    for contatto in sorted(lista_contatti, key = operator.itemgetter("Nome")):
        treeview.insert("", tk.END, values = [contatto["Nome"], contatto["Telefono"], contatto["Email"], contatto["Indirizzo"]])

def present_contact(contatto):
    # return "%-20s %-15s %-30s %-20s" %(contatto["Nome"], contatto["Telefono"], contatto["Email"], contatto["Indirizzo"])
    return f"{contatto['Nome']:20}{contatto['Telefono']:15}{contatto['Email']:30}{contatto['Indirizzo']:20}"

def hide_initial_empty_column_tree(treeview: ttk.Treeview):
    treeview.column("#0", width = 0, stretch = tk.NO)
    
def set_treeview(treeview: ttk.Treeview):
    treeview.heading("Nome", text = "Nome", anchor = tk.W)
    treeview.heading("Telefono", text = "Telefono", anchor = tk.W)
    treeview.heading("Email", text = "Email", anchor = tk.W)
    treeview.heading("Indirizzo", text = "Indirizzo", anchor = tk.W)
    treeview.column("Nome", width = 150)
    treeview.column("Telefono", width = 100)
    treeview.column("Email", width = 200)
    treeview.column("Indirizzo", width = 150)

# ***** FUNCTIONS DB ******
def db_connect():
    conn = sqlite3.connect("rubrica.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS CONTATTI(name VARCHAR(255), telefono VARCHAR(255), email VARCHAR(255), address VARCHAR(255))")
    return conn, cursor

def load_contact():
    """
    Load old contacts in frame called 'Contatti salvati' and add to 'rubrica' these old contacts.
    """
    result = cursor.execute("SELECT * FROM CONTATTI")
    contacts_saved = result.fetchall()  # lista di tuple
    contacts_saved_dict = []    # lista di dizionari
    for contatto in contacts_saved:
        contatto_dict = {"Nome":contatto[0], "Telefono": contatto[1], "Email": contatto[2], "Indirizzo": contatto[3]}
        rubrica.append(contatto_dict)
        contacts_saved_dict.append(contatto_dict)
    print_contacts(contacts_saved_dict, treeview_save)

rubrica = []    # lista inizialmente vuota
rubrica_session = []

window = tk.Tk()
window.title("Rubrica")
window.configure(bg = "#172026")

ttk.Style().configure("Treeview.Heading", font = ("Verdana", 9, "bold"))
ttk.Style().configure("Treeview")

header_label = tk.Label(window, text = "Rubrica Telefonica", font = ('Verdana', 20, 'bold'), fg = "#04BFAD", bg = "#172026")
header_label.grid(row = 0, column = 0, columnspan = 2, pady = (60, 15))

# ***** GUI *****
# 1. NEW CONTACTS MANAGEMENT
frame_add = tk.LabelFrame(window, text = "Aggiungi nuovo contatto", font = ("Verdana", 11), fg = "#04BFAD", bg = "#172026")
frame_add.grid(row = 2, column = 0, padx = 10, sticky = "NESW")
# 1.1 NAME FIELD
image_persona = Image.open("icons8-persona-24.png")
photo_persona = ImageTk.PhotoImage(image_persona)
image_persona_label = tk.Label(frame_add, image = photo_persona, borderwidth = 0)
image_persona_label.grid(row = 0, column = 0, padx = (30, 10), pady = 5)
name_label = tk.Label(frame_add, text = "Nome", font = ("Verdana", 10), fg = "#04BFAD", bg = "#172026")
name_label.grid(row = 0, column = 1, pady = 5, sticky = "E")
asterisk_name_label = tk.Label(frame_add, text = "*", fg = "#ff0000", bg = "#172026")
asterisk_name_label.grid(row = 0, column = 2, pady = 5, sticky = "W")
name_entry = tk.Entry(frame_add, width = 60, font = ('Verdana', 10))
name_entry.grid(row = 0, column = 3, padx = (10, 10), pady = 5)

name_canvas = tk.Canvas(frame_add, width = 20, height = 20, bg = "#172026", highlightthickness = 0)
name_canvas.grid(row = 0, column = 4, padx = (0, 30), pady = 5)
image_mic1 = Image.open("icons8-microfono-24.png")
photo_mic1 = ImageTk.PhotoImage(image_mic1)
image_item_mic1 = name_canvas.create_image(10, 10, image = photo_mic1)
name_canvas.photo_mic1 = photo_mic1

# 1.2 TELEPHONE FIELD
image_telephone = Image.open("icons8-telefono-24.png")
photo_telephone = ImageTk.PhotoImage(image_telephone)
image_telephone_label = tk.Label(frame_add, image = photo_telephone, borderwidth = 0)
image_telephone_label.grid(row = 1, column = 0, padx = (30, 10), pady = 5)
telephone_label = tk.Label(frame_add, text = "Telefono", font = ("Verdana", 10), fg = "#04BFAD", bg = "#172026")
telephone_label.grid(row = 1, column = 1, pady = 5, sticky = "E")
asterisk_telephone_label = tk.Label(frame_add, text = "*", fg = "#ff0000", bg = "#172026")
asterisk_telephone_label.grid(row = 1, column = 2, pady = 5, sticky = "W")
telephone_entry = tk.Entry(frame_add, width = 60, font = ('Verdana', 10))
telephone_entry.grid(row = 1, column = 3, padx = (10, 10), pady = 5)

telephone_canvas = tk.Canvas(frame_add, width = 20, height = 20, bg = "#172026", highlightthickness = 0)
telephone_canvas.grid(row = 1, column = 4, padx = (0, 30), pady = 5)
image_mic2 = Image.open("icons8-microfono-24.png")
photo_mic2 = ImageTk.PhotoImage(image_mic2)
image_item_mic2 = telephone_canvas.create_image(10, 10, image = photo_mic2)
telephone_canvas.photo_mic2 = photo_mic2

# 1.3 EMAIL FIELD
image_email = Image.open("icons8-nuovo-messaggio-24.png")
photo_email = ImageTk.PhotoImage(image_email)
image_email_label = tk.Label(frame_add, image = photo_email, borderwidth = 0)
image_email_label.grid(row = 2, column = 0, padx = (30, 10), pady = 5)
email_label = tk.Label(frame_add, text = "Email", font = ("Verdana", 10), fg = "#04BFAD", bg = "#172026")
email_label.grid(row = 2, column = 1, pady = 5, sticky = "E")
asterisk_email_label = tk.Label(frame_add, text = "*", fg = "#ff0000", bg = "#172026")
asterisk_email_label.grid(row = 2, column = 2, pady = 5, sticky = "W")
email_entry = tk.Entry(frame_add, width = 60, font = ('Verdana', 10))
email_entry.grid(row = 2, column = 3, padx = (10, 10), pady = 5)

email_canvas = tk.Canvas(frame_add, width = 20, height = 20, bg = "#172026", highlightthickness = 0)
email_canvas.grid(row = 2, column = 4, padx = (0, 30), pady = 5)
image_mic3 = Image.open("icons8-microfono-24.png")
photo_mic3 = ImageTk.PhotoImage(image_mic3)
image_item_mic3 = email_canvas.create_image(10, 10, image = photo_mic3)
email_canvas.photo_mic3 = photo_mic3

# 1.4 ADDRESS FIELD
image_address = Image.open("icons8-casa-24.png")
photo_address = ImageTk.PhotoImage(image_address)
image_address_label = tk.Label(frame_add, image = photo_address, borderwidth = 0)
image_address_label.grid(row = 3, column = 0, padx = (30, 10), pady = 5)
address_label = tk.Label(frame_add, text = "Indirizzo", font = ("Verdana", 10), fg = "#04BFAD", bg = "#172026")
address_label.grid(row = 3, column = 1, pady = 5, sticky = "E")
asterisk_address_label = tk.Label(frame_add, text = "*", fg = "#ff0000", bg = "#172026")
asterisk_address_label.grid(row = 3, column = 2, pady = 5, sticky = "W")
address_entry = tk.Entry(frame_add, width = 60, font = ('Verdana', 10))
address_entry.grid(row = 3, column = 3, padx = (10, 10), pady = 5)

address_canvas = tk.Canvas(frame_add, width = 20, height = 20, bg = "#172026", highlightthickness = 0)
address_canvas.grid(row = 3, column = 4, padx = (0, 30), pady = 5)
image_mic4 = Image.open("icons8-microfono-24.png")
photo_mic4 = ImageTk.PhotoImage(image_mic4)
image_item_mic4 = address_canvas.create_image(10, 10, image = photo_mic4)
address_canvas.photo_mic4 = photo_mic4

# 1.5 BUTTON
add_button = tk.Button(frame_add, text = "Aggiungi", bg = "#04BFAD", fg = "#172026", 
                       padx = 30, pady = 5, command = add_contact)
add_button.grid(row = 4, column = 0, columnspan = 4, padx = 10, pady = 10)

# 2. CONTACTS MANAGEMENT ADDED IN THIS SESSION
frame_contacts = tk.LabelFrame(window, text = "Contatti aggiunti in questa sessione", font = ("Verdana", 11), fg = "#04BFAD", bg = "#172026")
frame_contacts.grid(row = 3, column = 0, padx = 10, pady = (0, 10), sticky = "NESW")
# 2.1 TREEVIEW FOR CLEAR AND HIERARCHICAL DATA PRESENTATION
treeview_contacts = ttk.Treeview(frame_contacts, columns = ["Nome", "Telefono", "Email", "Indirizzo"])
treeview_contacts.grid(row = 0, column = 0, rowspan = 2, columnspan = 2, padx = (10, 0), pady = 10, sticky = "NSEW")
set_treeview(treeview_contacts)
hide_initial_empty_column_tree(treeview_contacts)
# 2.2 SCROLLBAR FOR MORE CONTACTS
scrollbar_contacts = tk.Scrollbar(frame_contacts)
scrollbar_contacts.grid(row = 0, column = 3, rowspan = 2, padx = (5, 10), pady = 10, sticky = "NS") 
treeview_contacts.config(yscrollcommand = scrollbar_contacts.set)
scrollbar_contacts.config(command = treeview_contacts.yview)

# 3. EXISTING CONTACTS MANAGEMENT
frame_save = tk.LabelFrame(window, text = "Contatti salvati", font = ("Verdana", 11), fg = "#04BFAD", bg = "#172026")
frame_save.grid(row = 2, column = 1, padx = (0, 10), sticky = "NESW")
treeview_save = ttk.Treeview(frame_save, columns = ["Nome", "Telefono", "Email", "Indirizzo"])
treeview_save.grid(row = 0, column = 0, padx = (10, 0), pady = 10)
set_treeview(treeview_save)
hide_initial_empty_column_tree(treeview_save)

scrollbar_save = tk.Scrollbar(frame_save)
scrollbar_save.grid(row = 0, column = 1, padx = (5, 10), pady = 10, sticky = "NS") 
treeview_save.config(yscrollcommand = scrollbar_save.set)
scrollbar_save.config(command = treeview_save.yview)

# 4. SEARCH AND REMOVE CONTACTS
frame_sr = tk.LabelFrame(window, text = "Ricerca/Rimuovi", font = ("Verdana", 11), fg = "#04BFAD", bg = "#172026")
frame_sr.grid(row = 3, column = 1, padx = (0, 10), pady = (0, 10), sticky = "NESW")
wanted_entry = tk.Entry(frame_sr, width = 50)
wanted_entry.grid(row = 0, column = 0, padx = 10)
search_button = tk.Button(frame_sr, text = "Cerca", bg = "#04BFAD", fg = "#172026", 
                          padx = 5, width = 10, command = search_contact)
search_button.grid(row = 0, column = 1, padx = 10, pady = 5)
remove_button = tk.Button(frame_sr, text = "Rimuovi", bg = "#04BFAD", fg = "#172026", 
                          padx = 5, width = 10, command = remove_contact)
remove_button.grid(row = 0, column = 2, padx = (0, 10), pady = 5)
treeview_sr = ttk.Treeview(frame_sr, columns = ["Nome", "Telefono", "Email", "Indirizzo"])
treeview_sr.grid(row = 1, column = 0, columnspan = 3, padx = 10, pady = 10, sticky = "WE")
set_treeview(treeview_sr)
hide_initial_empty_column_tree(treeview_sr)

conn, cursor = db_connect()
load_contact()

qta_numeri_label = tk.Label(window, text = f"{count_numbers()} contatti con numeri telefonici", 
                            font = ('Verdana', 10), fg = "#04BFAD", bg = "#172026")
qta_numeri_label.grid(row = 1, column = 0, columnspan = 2, pady = (0, 50))

for row in range(0, 5):
    frame_add.grid_rowconfigure(row, weight = 1)

for row in range(0, 2):
    frame_contacts.grid_rowconfigure(row, weight = 1)
    frame_sr.grid_rowconfigure(row, weight = 1)

frame_save.grid_rowconfigure(0, weight = 1)

frame_add.grid_columnconfigure(0, weight = 1)
frame_add.grid_columnconfigure(1, weight = 1)
frame_contacts.grid_columnconfigure(0, weight = 1)
frame_save.grid_columnconfigure(0, weight = 1)
frame_sr.grid_columnconfigure(0, weight = 1)
frame_sr.grid_columnconfigure(1, weight = 1)
frame_sr.grid_columnconfigure(2, weight = 1)

voice_input_button = tk.Button(frame_add, text="Inserisci tramite Voce", bg="#04BFAD", fg="#172026",
                               padx=20, pady=5, command=voice_input)
voice_input_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)


window.mainloop()