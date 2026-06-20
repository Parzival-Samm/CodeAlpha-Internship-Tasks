import glob
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, Activation
from tensorflow.keras.utils import to_categorical
from music21 import converter, instrument, note, chord, stream

# --- Configuration ---
MIDI_DIR = "midi_songs/*.mid"
SEQUENCE_LENGTH = 100  # Number of previous notes the model uses to predict the next one
EPOCHS = 50
BATCH_SIZE = 64

# ==========================================
# STEP 1 & 2: Collect & Preprocess Data
# ==========================================
def get_notes():
    """Parses MIDI files and extracts sequences of notes and chords."""
    print("🎵 Extracting notes from MIDI files...")
    notes = []
    
    for file in glob.glob(MIDI_DIR):
        midi = converter.parse(file)
        
        # Group parts by instrument
        parts = instrument.partitionByInstrument(midi)
        if parts: # If it has instrument parts, grab the first one (usually piano)
            notes_to_parse = parts.parts[0].recurse()
        else: # Otherwise, it's a flat structure
            notes_to_parse = midi.flat.notes
            
        for element in notes_to_parse:
            if isinstance(element, note.Note):
                # Extract the pitch (e.g., C4, F#5)
                notes.append(str(element.pitch))
            elif isinstance(element, chord.Chord):
                # Extract chords and separate notes with a dot (e.g., 4.15.7)
                notes.append('.'.join(str(n) for n in element.normalOrder))
                
    return notes

def prepare_sequences(notes, n_vocab):
    """Prepares the input sequences and the corresponding outputs for the network."""
    print("⚙️ Preparing sequences for training...")
    
    # Create a dictionary mapping string pitches to integers
    pitches = sorted(set(item for item in notes))
    note_to_int = dict((note, number) for number, note in enumerate(pitches))
    
    network_input = []
    network_output = []
    
    # Create input sequences and the corresponding next note
    for i in range(0, len(notes) - SEQUENCE_LENGTH, 1):
        sequence_in = notes[i:i + SEQUENCE_LENGTH]
        sequence_out = notes[i + SEQUENCE_LENGTH]
        network_input.append([note_to_int[char] for char in sequence_in])
        network_output.append(note_to_int[sequence_out])
        
    n_patterns = len(network_input)
    
    # Reshape the input into a format compatible with LSTM layers
    X = np.reshape(network_input, (n_patterns, SEQUENCE_LENGTH, 1))
    # Normalize input
    X = X / float(n_vocab)
    # One-hot encode the output
    y = to_categorical(network_output, num_classes=n_vocab)
    
    return X, y, network_input, pitches

# ==========================================
# STEP 3: Build the Deep Learning Model
# ==========================================
def create_network(X, n_vocab):
    """Builds a stacked LSTM model."""
    print("🧠 Building the LSTM Model...")
    model = Sequential()
    
    # First LSTM Layer
    model.add(LSTM(256, input_shape=(X.shape[1], X.shape[2]), return_sequences=True))
    model.add(Dropout(0.3))
    
    # Second LSTM Layer
    model.add(LSTM(256))
    model.add(Dropout(0.3))
    
    # Output Layer
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
    return model

# ==========================================
# STEP 4 & 5: Generate Music & Save to MIDI
# ==========================================
def generate_notes(model, network_input, pitches, n_vocab):
    """Generates a sequence of notes based on the trained model."""
    print("🎹 Generating new music...")
    
    # Map integers back to strings
    int_to_note = dict((number, note) for number, note in enumerate(pitches))
    
    # Pick a random starting sequence from our input data
    start = np.random.randint(0, len(network_input)-1)
    pattern = network_input[start]
    prediction_output = []
    
    # Generate 100 notes
    for note_index in range(100):
        prediction_input = np.reshape(pattern, (1, len(pattern), 1))
        prediction_input = prediction_input / float(n_vocab)
        
        prediction = model.predict(prediction_input, verbose=0)
        
        # Get the index of the highest probability prediction
        index = np.argmax(prediction)
        result = int_to_note[index]
        prediction_output.append(result)
        
        # Shift the pattern over by one
        pattern.append(index)
        pattern = pattern[1:len(pattern)]
        
    return prediction_output

def create_midi(prediction_output, filename="ai_generated_music.mid"):
    """Converts the generated string array back into MIDI format."""
    print(f"💾 Saving generated music to {filename}...")
    offset = 0
    output_notes = []
    
    # Create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        # Pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        # Pattern is a single note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)
            
        # Increase offset each iteration so notes don't stack perfectly on top of each other
        offset += 0.5
        
    midi_stream = stream.Stream(output_notes)
    midi_stream.write('midi', fp=filename)
    print("✅ Process complete!")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == '__main__':
    # 1 & 2. Extract and preprocess
    notes = get_notes()
    n_vocab = len(set(notes))
    
    if n_vocab == 0:
        print("❌ Error: No notes extracted. Please add .mid files to the 'midi_songs' directory.")
        exit()
        
    X, y, network_input, pitches = prepare_sequences(notes, n_vocab)
    
    # 3. Build model
    model = create_network(X, n_vocab)
    
    # 4. Train the model
    print("⏳ Training model (this may take a while depending on your GPU/CPU)...")
    model.fit(X, y, epochs=EPOCHS, batch_size=BATCH_SIZE)
    
    # 5. Generate and save
    generated_sequence = generate_notes(model, network_input, pitches, n_vocab)
    create_midi(generated_sequence)