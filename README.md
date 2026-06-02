# Dokumentacja projektu

## Terminarz Medyczny – System Zarządzania Wizytami w Przychodni

### Autorzy projektu

* Szymon Podlasiak
* Marcin Kwiatkowski
* Dawid Dykto

### Technologia

* Python
* Flask
* HTML5
* CSS3
* JavaScript
* SQLite

---

# 1. Cel projektu

Celem projektu było stworzenie aplikacji użytkowej umożliwiającej zarządzanie wizytami lekarskimi w przychodni. System pozwala na rejestrację i logowanie użytkowników, zarządzanie kontami pacjentów i lekarzy oraz rezerwowanie terminów wizyt.

Projekt został wykonany zgodnie z założeniami programowania obiektowego oraz wymaganiami dotyczącymi trwałego zapisu danych.

---

# 2. Opis działania aplikacji

Aplikacja umożliwia:

### Pacjentowi:

* rejestrację konta
* logowanie do systemu
* przeglądanie lekarzy
* umawianie wizyt
* anulowanie wizyt
* przegląd historii wizyt

### Lekarzowi:

* logowanie do systemu
* podgląd harmonogramu wizyt
* zarządzanie statusem wizyty
* dodawanie notatek do wizyty

### Administratorowi:

* zarządzanie lekarzami
* podgląd wszystkich wizyt
* zarządzanie użytkownikami

---

# 3. Programowanie obiektowe

W projekcie zastosowano podejście obiektowe.

### Klasy:

#### User

Reprezentuje użytkownika systemu.

Atrybuty:

* id
* email
* password
* role

#### Patient

Dziedziczy po klasie User.

Dodatkowe atrybuty:

* imię
* nazwisko
* PESEL
* telefon

#### Doctor

Dziedziczy po klasie User.

Dodatkowe atrybuty:

* specjalizacja
* gabinet

#### Appointment

Reprezentuje wizytę.

Atrybuty:

* pacjent
* lekarz
* data wizyty
* status
* notatki

### Zastosowane elementy OOP

* klasy i obiekty
* konstruktory
* dziedziczenie
* enkapsulacja danych
* relacje pomiędzy obiektami

---

# 4. Baza danych

Do przechowywania danych wykorzystano bazę SQLite.

### Tabela users

Przechowuje dane logowania użytkowników.

Pola:

* id
* email
* password
* role
* created_at

### Tabela patients

Przechowuje dane pacjentów.

Pola:

* id
* user_id
* first_name
* last_name
* pesel
* phone

### Tabela doctors

Przechowuje dane lekarzy.

Pola:

* id
* user_id
* first_name
* last_name
* specialization
* room

### Tabela appointments

Przechowuje informacje o wizytach.

Pola:

* id
* patient_id
* doctor_id
* appointment_date
* status
* notes

### Tabela doctor_schedule

Przechowuje grafik pracy lekarzy.

Pola:

* id
* doctor_id
* day_of_week
* start_time
* end_time

---

# 5. Obsługa błędów

Aplikacja została zabezpieczona przed błędami użytkownika.

Przykładowe zabezpieczenia:

* brak możliwości pozostawienia pustych pól wymaganych
* walidacja adresu e-mail
* walidacja numeru PESEL
* blokowanie dat z przeszłości
* blokowanie podwójnej rezerwacji tego samego terminu
* sprawdzanie dostępności lekarza
* obsługa wyjątków podczas operacji na bazie danych

W przypadku błędnych danych użytkownik otrzymuje czytelny komunikat o błędzie.

---

# 6. Trwałość danych

Dane nie są zapisane na stałe w kodzie programu.

Wszystkie informacje są przechowywane w bazie danych SQLite.

Po ponownym uruchomieniu aplikacji:

* użytkownicy pozostają zapisani
* wizyty pozostają zapisane
* harmonogram lekarzy pozostaje zapisany

---

# 7. Interfejs użytkownika

Interfejs został wykonany przy użyciu HTML, CSS oraz JavaScript.

Zawiera:

* formularz logowania
* formularz rejestracji
* panel pacjenta
* panel lekarza
* panel administratora
* formularz umawiania wizyt
* listę wizyt

Projekt został przygotowany w sposób umożliwiający wygodne korzystanie przez użytkownika.

---

# 8. Podział obowiązków

### Szymon Podlasiak

* projekt bazy danych
* implementacja backendu
* implementacja logiki wizyt
* integracja aplikacji

### Marcin Kwiatkowski

* projekt interfejsu użytkownika
* formularze
* obsługa interakcji użytkownika

### Dawid Dykto

* testowanie aplikacji
* walidacja danych
* dokumentacja
* scenariusze testowe

---

# 9. Wnioski

Projekt pozwolił na praktyczne wykorzystanie programowania obiektowego, pracy zespołowej oraz tworzenia aplikacji wykorzystujących bazę danych.

Podczas realizacji wykorzystano:

* klasy i obiekty
* relacyjne bazy danych
* obsługę wyjątków
* walidację danych
* architekturę klient-serwer

Efektem końcowym jest działająca aplikacja do zarządzania wizytami w przychodni lekarskiej.
