import streamlit as st
import spacy
import pandas as pd
import matplotlib.pyplot as plt
from processing import process_text, render_entities, get_default_input, get_entity_colors, get_entity_label_examples

# Page configuration - https://docs.streamlit.io/library/api-reference/config 
st.set_page_config(
  page_title='Named Entity Visualizer',
  page_icon='🔍',
)

# Load models only when necessary - https://docs.streamlit.io/library/advanced-features/caching
@st.cache_resource
def load_model(model):
    return spacy.load(model)

# Load pre-trained models - https://spacy.io/models/
model_en = load_model('en_core_web_sm')
model_fr = load_model('fr_core_news_sm')
model_de = load_model('de_core_news_sm')
model_nl = load_model('nl_core_news_sm')
model_es = load_model('es_core_news_sm')

# Load entity labels - https://spacy.io/api/language#get_pipe
entity_labels = {
    'en_core_web_sm': model_en.get_pipe('ner').labels,
    'fr_core_news_sm': model_fr.get_pipe('ner').labels,
    'de_core_news_sm': model_de.get_pipe('ner').labels,
    'nl_core_news_sm': model_nl.get_pipe('ner').labels,
    'es_core_news_sm': model_es.get_pipe('ner').labels,
}

# Load entity colors
entity_colors = get_entity_colors()

# Set default model to session state - https://docs.streamlit.io/library/api-reference/session-state
if 'current_model' not in st.session_state:
    st.session_state.current_model = 'en_core_web_sm'
    
# Set default entity labels to session state - https://docs.streamlit.io/library/api-reference/session-state
if 'selected_options' not in st.session_state:
    st.session_state.selected_options = entity_labels[st.session_state.current_model]

# Sidebar title
title = '<p style="color: Indigo; font-size: 54px; font-family: Segoe UI;">NEV</p>'
st.sidebar.markdown(title, unsafe_allow_html=True)

# Sidebar description
description = '<p style="font-size: 18px">NEV short for <span style="color: Indigo; font-weight: bold;">Named Entity Visualizer</span> is a tool to visualize entities found in unstructured text. Entities are extracted from input text using  <span style="color: Indigo; font-weight: bold;">Named Entity Recognition (NER)</span> and then linked to concepts on  <span style="color: Indigo; font-weight: bold;">Wikidata</span> knowledge graph using <span style="color: Indigo; font-weight: bold;">Named Entity Linking (NEL)</span>. This process is executed using a pre-trained model with NLP pipeline.</p>'
st.sidebar.markdown(description, unsafe_allow_html=True)

# Sidebar model selection
model_options = {
  'en_core_web_sm': model_en, 
  'fr_core_news_sm': model_fr, 
  'de_core_news_sm': model_de,
  'nl_core_news_sm': model_nl,
  'es_core_news_sm': model_es,
  }
st.session_state.current_model = st.sidebar.selectbox('Select a model', model_options.keys())

# Sidebar model description
st.sidebar.title('Model description')
selected_model = model_options[st.session_state.current_model]
model_description = selected_model.meta['description']
model_version = selected_model.meta['version']
model_info = f'<p style="font-size: 16px"><b>{st.session_state.current_model}:</b> <code>{model_version}</code>{model_description}</p>'
st.sidebar.markdown(model_info, unsafe_allow_html=True)

# Named entities selection
st.sidebar.title('Named Entity Labels')
container = st.sidebar.container()
all = st.sidebar.toggle('Select all labels', value=True)

# Label Scheme Explanation
st.sidebar.title('Model Label Scheme Explanation')
with st.sidebar.expander('See explanation and examples', expanded=False):
  for label in entity_labels[st.session_state.current_model]:
    st.markdown(f'**{label}** - {spacy.explain(label)}')
    st.markdown(f'- *{get_entity_label_examples().get(label, "No example available.")}*')

# Select all entities by default, else select only the ones that are already selected
if all:
  st.session_state.selected_options = container.multiselect('Select entity labels to display', entity_labels[st.session_state.current_model], default=entity_labels[st.session_state.current_model])
else: 
  st.session_state.selected_options = container.multiselect('Select entity labels to display', entity_labels[st.session_state.current_model])

# Set different colors for each entity
for label, color in entity_colors.items():
  st.sidebar.markdown(
    f"""
    <style>
        span[data-baseweb="tag"]:has(span[title={label}]) {{
            background-color: {color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)
  
# Input text to analyze
st.header('Input text')
input_text = st.text_area('Text to analyze', get_default_input(), height=250)
if not input_text.strip():
  st.warning('Please enter some text to analyze.', icon="⚠️")

# Named Entities - https://spacy.io/usage/visualizers
st.header('Named Entity Recognition')
with st.container(border=False):
  if not input_text.strip():
    st.error('Named entities cannot be extracted from empty text!', icon='❌')
  else:
    doc = process_text(input_text, st.session_state.current_model)
    ent_html = render_entities(doc, st.session_state.selected_options)
    st.markdown(ent_html, unsafe_allow_html=True)
    if not doc.ents:
      st.warning('No entities found in the input text.', icon='⚠️')
    elif not st.session_state.selected_options:
      st.warning('No entity labels selected to display.', icon='⚠️')

# Table of entities
st.header('Named Entity Linking')
table_data = []

if not input_text.strip():
  st.error('Named entities cannot be extracted from empty text!', icon='❌')
elif not doc.ents:
  st.warning('No entities found in the input text.', icon='⚠️')
elif not st.session_state.selected_options:
  st.warning('No entity labels selected to display.', icon='⚠️')
else:
  input_entity_labels = [ent.label_ for ent in doc.ents]
  # Check if any selected entity labels match the ones found in the input text
  if not any(label in input_entity_labels for label in st.session_state.selected_options):
    st.warning('No entity labels match the ones found in the input text.', icon='⚠️')
  else:
    # Create a dataframe of entities
    for ent in doc.ents:
      if ent.label_ in st.session_state.selected_options:
        structure = {
          'Entity': ent.text,
          'Label': ent.label_,
          'ID': ent._.kb_qid if hasattr(ent._, 'kb_qid') else 'NaN',
          'Wikidata URL': ent._.url_wikidata if hasattr(ent._, 'url_wikidata') else 'NaN'
        }
        table_data.append(structure)
    df = pd.DataFrame(table_data)

    # Container for table
    with st.container(border=False):
      st.data_editor(
        df,
        column_config={
          'Wikidata URL': st.column_config.LinkColumn(),
        },
        hide_index=True,
        use_container_width=True,
      )

    # Get unique labels and their colors  
    unique_labels = df['Label'].unique()
    label_colors = [get_entity_colors().get(label, 'gray') for label in unique_labels]
    label_dict = dict(zip(unique_labels, label_colors))

    # Entity label distribution graph
    st.header('Entity Label Distribution')
    with st.container(border=False):
      fig, ax = plt.subplots()
      counts = df['Label'].value_counts()
      # Plot all entity labels and their counts
      counts.plot(kind='bar', color=[label_dict[label] for label in counts.index])
      ax.set_xlabel('Entity Label')
      ax.set_ylabel('Count')
      plt.xticks(rotation=45, ha='right')
      # Set y-axis ticks to natural numbers
      ax.set_yticks(range(int(counts.max()) + 1))
      st.pyplot(fig)