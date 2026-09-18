import streamlit as st
import pandas as pd

def calculate_cutting_plan(bar_length, kerf, grip_waste, parts_df):
    """
    bar_length: Total længde på en købt stang (mm)
    kerf: Savsnit / klingetykkelse - materialespild pr. snit (mm)
    grip_waste: Ubrugelig længde som maskinen kræver for at holde stangen (mm)
    parts_df: DataFrame med 'Længde (mm)' og 'Antal'
    """
    usable_length = bar_length - grip_waste
    
    # Skab en flad liste af alle de stykker, der skal skæres
    pieces = []
    for index, row in parts_df.iterrows():
        length = row['Længde (mm)']
        count = int(row['Antal'])
        if length > usable_length:
            st.error(f"Fejl: Et emne på {length} mm er længere end den brugbare stanglængde på {usable_length} mm!")
            return None
        pieces.extend([length] * count)
        
    # Sortér stykker fra længst til kortest (First Fit Decreasing - minimerer spild effektivt)
    pieces.sort(reverse=True)
    
    # Liste af stænger. Hver stang er et dictionary med tilbageværende brugbar længde og hvilke emner der er på den.
    bars = [] 
    
    for piece in pieces:
        placed = False
        for bar in bars:
            # Beregn hvor meget længde dette stykke vil tage på denne stang.
            # Hvis der allerede er skåret et stykke, skal der bruges et 'kerf' (savsnit) for at adskille dem.
            cost = piece if len(bar['pieces']) == 0 else kerf + piece
            
            if bar['remaining'] >= cost:
                bar['remaining'] -= cost
                bar['pieces'].append(piece)
                placed = True
                break
                
        if not placed:
            # Der var ikke plads på eksisterende stænger, så vi tager en ny stang
            bars.append({'remaining': usable_length - piece, 'pieces': [piece]})
            
    return bars

def main():
    st.set_page_config(page_title="Stang Skæreplan", page_icon="🪚", layout="wide")
    st.title("🪚 Beregner til Stangmateriale (Skæreplan)")
    st.markdown("Dette værktøj optimerer dit materialeforbrug ved at pakke dine ønskede emner mest effektivt ind i de rå stænger.")
    
    st.sidebar.header("Maskin- og Materialeindstillinger")
    bar_length = st.sidebar.number_input("Standard stanglængde (mm)", value=6000, step=100, min_value=100)
    kerf = st.sidebar.number_input("Savsnit / klinge tykkelse (mm)", value=3, step=1, min_value=0)
    grip_waste = st.sidebar.number_input("Maskinens gribekant / restspild (mm)", value=100, step=10, min_value=0)
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"Brugbar længde pr. stang:\n### **{bar_length - grip_waste} mm**")
    
    st.subheader("Indtast emner der skal skæres")
    st.markdown("Indtast de længder du har brug for, og mængden af hver. Du kan tilføje flere rækker nederst i tabellen.")
    
    # Startdata baseret på dit eksempel
    initial_data = pd.DataFrame({
        "Længde (mm)": [500, 750, 150],
        "Antal": [10, 30, 5]
    })
    
    edited_df = st.data_editor(
        initial_data,
        num_rows="dynamic",
        column_config={
            "Længde (mm)": st.column_config.NumberColumn(
                "Længde (mm)",
                help="Længden på det emne du skal bruge",
                min_value=1,
                step=1,
                required=True,
            ),
            "Antal": st.column_config.NumberColumn(
                "Antal",
                help="Hvor mange af denne længde skal du bruge?",
                min_value=1,
                step=1,
                required=True,
            )
        },
        hide_index=True,
        width=600
    )
    
    if st.button("Beregn Skæreplan", type="primary", use_container_width=True):
        # Fjern tomme rækker eller rækker med ugyldige tal
        valid_df = edited_df.dropna()
        valid_df = valid_df[(valid_df['Længde (mm)'] > 0) & (valid_df['Antal'] > 0)]
        
        if valid_df.empty:
            st.warning("Indtast venligst nogle længder og antal for at beregne.")
            return
            
        with st.spinner("Beregner optimal skæreplan..."):
            bars = calculate_cutting_plan(bar_length, kerf, grip_waste, valid_df)
        
        if bars is not None:
            # Statistik
            total_bars = len(bars)
            total_purchased_length = total_bars * bar_length
            
            used_length_for_parts = sum(valid_df['Længde (mm)'] * valid_df['Antal'])
            total_kerf_waste = sum([(len(b['pieces'])-1)*kerf for b in bars if len(b['pieces'])>0])
            total_grip_waste = total_bars * grip_waste
            total_rest_waste = sum([b['remaining'] for b in bars])
            
            st.markdown("---")
            st.success(f"### Resultat: Du skal bruge **{total_bars}** stænger.")
            
            # Kolonner for statistik
            col1, col2, col3 = st.columns(3)
            col1.metric("Brugt materiale (inkl. savsnit)", f"{(used_length_for_parts + total_kerf_waste) / 1000:.2f} m")
            col2.metric("Maskinspild i alt", f"{total_grip_waste / 1000:.2f} m")
            col3.metric("Rene afskårne rester i alt", f"{total_rest_waste / 1000:.2f} m")
            
            st.markdown("---")
            st.subheader("📋 Detaljeret Skæreplan")
            
            for i, bar in enumerate(bars):
                used_percentage = ((bar_length - grip_waste - bar['remaining']) / bar_length) * 100
                
                with st.expander(f"Stang {i+1} (Udnyttelse: {used_percentage:.1f}%)", expanded=True):
                    # Visuel repræsentation af stykkerne
                    pieces_str = " ➔ ".join([f"**{p}**mm" for p in bar['pieces']])
                    st.markdown(f"**Skær i rækkefølge:** {pieces_str}")
                    
                    st.write(f"- Antal emner skåret af denne stang: **{len(bar['pieces'])} stk.**")
                    st.write(f"- Ubrugt rest (kan evt. gemmes): **{bar['remaining']} mm**")

if __name__ == "__main__":
    main()
