"""Navigation categories only. Original evidence and exact plan identities survive."""
import re

SPECIALTIES = {
    'Cancer care': ['Cancer','Cancer Care','Oncology','Hematology/Oncology'],
    'Heart and vascular care': ['Cardiology','Cardiovascular Care','Heart and Vascular Care','Cardiology and Heart Surgery'],
    'Orthopedics': ['Orthopedics','Orthopaedics','Orthopedic Surgery'],
    'Brain, nerves and neurosurgery': ['Neurology','Neurosciences','Neurology and Neurosurgery','Neurosurgery'],
    'Digestive health': ['Gastroenterology','Gastroenterology and GI Surgery','Digestive Health'],
    'Lung and respiratory care': ['Pulmonary','Pulmonology','Pulmonology and Lung Surgery','Pulmonary Medicine'],
    'Diabetes and endocrinology': ['Diabetes','Endocrinology','Diabetes and Endocrinology'],
    'Mental and behavioral health': ['Psychiatry','Behavioral Health','Mental Health','Psychiatric Services'],
    'Ear, nose and throat': ['Ear Nose and Throat (ENT)','Otolaryngology','Ear, Nose and Throat'],
    'Kidney care': ['Nephrology','Kidney Care'],
    'Rehabilitation': ['Rehabilitation','Physical Medicine and Rehabilitation','Pediatric Rehabilitation'],
}
# Broad navigation categories only; age group, setting and exact source label
# remain visible in each evidence record. No insurance plan aliasing occurs.
SPECIALTIES['Cancer care'] += ['Cancer Care Center','Cancer & Blood Disorders','Comprehensive Cancer Center']
SPECIALTIES['Heart and vascular care'] += ['Heart Care','Cardiovascular','Cardiology Services','Cardiology/Cardio Respiratory','Heart & Vascular Center','Heart & vascular care','Cardiology & Cardiac Surgery']
SPECIALTIES['Orthopedics'] += ['Orthopedic Surgery and Treatment','Musculoskeletal Center']
SPECIALTIES['Brain, nerves and neurosurgery'] += ['Neuroscience','Neuroscience Center','Neurology & Neurosurgery']
SPECIALTIES['Digestive health'] += ['Digestive Disorders','Gastroenterology (GI)','Gastroenterology Services','Digestive Health (Gastroenterology)']
SPECIALTIES['Lung and respiratory care'] += ['Pulmonology (Adult)','Pulmonology (Lung Health)','Respiratory Care']
SPECIALTIES['Diabetes and endocrinology'] += ['Diabetes Clinic','Diabetes & Endocrinology','Diabetes Education/Treatment']
SPECIALTIES['Mental and behavioral health'] += ['Behavioral Health Unit','Adult Mental Health Program','Behavioral Medicine','Outpatient Behavioral Health','Psychiatry & Behavioral Health','Geriatric Psychiatric']
SPECIALTIES['Kidney care'] += ['Nephrology (Hypertension)','Hemodialysis']
SPECIALTIES['Rehabilitation'] += ['Physical Therapy/Rehabilitation Services','Rehabilitation Services','Rehabilitation Medicine','Pediatric Rehabilitation and Therapy','Therapy Services','Physical Therapy','Rehabilitative Services']
SPECIALTIES['Dental care'] = ['Dental','Dentistry']
SPECIALTIES['Obstetrics and gynecology'] = ['Gynecology','OB/GYN','Obstetrician-Gynecologist (OB-GYN)','Labor and Delivery',"Women's health"]
SPECIALTIES['Rheumatology'] = ['Rheumatology','Rheumatology Clinic']
SPECIALTIES['Primary care'] = ['Primary Care']
SPECIALTIES['Allergy and immunology'] = ['Allergy and Immunology','Allergy/Immunology']
SPECIALTIES['Stroke care'] = ['Stroke Center','stroke care']
SPECIALTIES['Infectious diseases'] = ['Infectious Disease','Infectious Diseases']


def specialty_category(name):
    for label, aliases in SPECIALTIES.items():
        if name.casefold() in {a.casefold() for a in [label,*aliases]}: return label
    return name

def specialty_names(category, names):
    target=specialty_category(category)
    return [name for name in names if specialty_category(name)==target]

def insurance_carrier(name):
    # Prefix classification never makes two distinct plan strings equivalent.
    value=re.sub(r'^20\d{2}\s+', '', name.strip()).casefold()
    for carrier,prefixes in {
        'Aetna': ('aetna',),
        'Blue Cross Blue Shield': ('blue cross','bcbs','blue choice','blue precision','bluecare','blue advantage'),
        'Cigna': ('cigna',),
        'UnitedHealthcare': ('united healthcare','united health care','unitedhealthcare','uhc '),
        'Humana': ('humana',),
        'Molina Healthcare': ('molina',),
        'Meridian': ('meridian',),
        'CountyCare': ('countycare','county care'),
        'Ambetter': ('ambetter',),
        'Devoted Health': ('devoted health',),
        'University of Chicago Health Plan': ('university of chicago health plan',),
    }.items():
        if value.startswith(prefixes): return carrier
    return 'Other / carrier not categorized'
