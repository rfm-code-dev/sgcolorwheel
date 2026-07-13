import streamlit as st
import colorsys
import matplotlib.pyplot as plt
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sega Genesis / Mega Drive Color Wheel", page_icon="🎮", layout="wide")

st.title("🎮 Sega Genesis / Mega Drive Color Wheel")
st.markdown("Create and calculate color harmonies locked strictly to the **512 colors (9-bit VDP RGB)** of the original hardware.")

# --- INJECT CUSTOM CSS TO REMOVE ROLLOVER AND FORCE PERFECT ALIGNMENT ---
st.markdown("""
    <style>
        div[data-testid="stColorPicker"] {
            pointer-events: none !important;
            cursor: default !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stColorPicker"] {
            pointer-events: auto !important;
        }
        div[data-testid="stHorizontalBlock"] button {
            display: block !important;
            margin: 0 auto !important;
            padding: 2px 4px !important;
            width: 100% !important;
            text-align: center !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- HARDWARE TECHNICAL CONSTANTS ---
VDP_STEPS = (0, 36, 73, 109, 146, 182, 219, 255)

def quantize_to_genesis(rgb):
    """Snaps any standard RGB color to the nearest native Sega Genesis VDP color."""
    return tuple(min(VDP_STEPS, key=lambda x: abs(x - c)) for c in rgb)

def rgb_to_sgdk_hex(rgb):
    """Converts RGB to native SGDK C format (0x0BGR) using 3 nibbles."""
    r, g, b = rgb
    r_vdp = VDP_STEPS.index(r) * 2
    g_vdp = VDP_STEPS.index(g) * 2
    b_vdp = VDP_STEPS.index(b) * 2
    vdp_value = (b_vdp << 8) | (g_vdp << 4) | r_vdp
    return f"0x{vdp_value:04X}"

def rgb_to_asm_hex(rgb):
    """Converts RGB to traditional Assembly 68k format ($0BGR)."""
    r, g, b = rgb
    r_vdp = VDP_STEPS.index(r) * 2
    g_vdp = VDP_STEPS.index(g) * 2
    b_vdp = VDP_STEPS.index(b) * 2
    vdp_value = (b_vdp << 8) | (g_vdp << 4) | r_vdp
    return f"${vdp_value:04X}"

def calculate_harmonies(base_rgb, angle, sat_mod=1.0, val_mod=1.0):
    """Rotates the Hue in HSV space, applies modifiers, and quantizes back to 9-bit RGB."""
    r, g, b = [c / 255.0 for c in base_rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    h_new = (h + (angle / 360.0)) % 1.0
    s_new = max(0.0, min(1.0, s * sat_mod))
    v_new = max(0.0, min(1.0, v * val_mod))
    
    r_res, g_res, b_res = colorsys.hsv_to_rgb(h_new, s_new, v_new)
    return quantize_to_genesis((int(r_res * 255), int(g_res * 255), int(b_res * 255)))

# --- INITIALIZE PALETTE ARRAY SLOTS AS FIXED 16 ELEMENT LIST ---
if "custom_palette" not in st.session_state or len(st.session_state.custom_palette) != 16:
    st.session_state.custom_palette = [None] * 16

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("🕹️ Harmony Panel")

harmony_rule = st.sidebar.selectbox(
    "Harmony Rule:",
    ["Analogous", "Monochromatic", "Triad", "Complementary", "Split Complementary", "Square", "Compound"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Native VDP Color Picker")

vdp_r = st.sidebar.slider("Red Channel (VDP)", min_value=0, max_value=7, value=0)
vdp_g = st.sidebar.slider("Green Channel (VDP)", min_value=0, max_value=7, value=6)
vdp_b = st.sidebar.slider("Blue Channel (VDP)", min_value=0, max_value=7, value=4)

base_genesis = (VDP_STEPS[vdp_r], VDP_STEPS[vdp_g], VDP_STEPS[vdp_b])
base_hex = f"#{base_genesis[0]:02X}{base_genesis[1]:02X}{base_genesis[2]:02X}"

st.sidebar.markdown("**Selected Base Preview:**")
st.sidebar.color_picker("Hardware Base Color", base_hex, key=f"sb_preview_{base_hex.replace('#', '')}")

# Extract active hardware brightness
r_norm, g_norm, b_norm = base_genesis[0]/255.0, base_genesis[1]/255.0, base_genesis[2]/255.0
_, _, dynamic_value = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)

# --- HARMONY RULE LOGIC ---
palette = []
if harmony_rule == "Analogous":
    palette = [
        calculate_harmonies(base_genesis, -60),
        calculate_harmonies(base_genesis, -30),
        base_genesis,
        calculate_harmonies(base_genesis, 30),
        calculate_harmonies(base_genesis, 60)
    ]
elif harmony_rule == "Monochromatic":
    palette = [
        calculate_harmonies(base_genesis, 0, sat_mod=0.2, val_mod=0.4),
        calculate_harmonies(base_genesis, 0, sat_mod=0.5, val_mod=0.7),
        base_genesis,
        calculate_harmonies(base_genesis, 0, sat_mod=0.8, val_mod=0.9),
        calculate_harmonies(base_genesis, 0, sat_mod=0.6, val_mod=1.2)
    ]
elif harmony_rule == "Triad":
    palette = [
        calculate_harmonies(base_genesis, 0, val_mod=0.6),
        base_genesis,
        calculate_harmonies(base_genesis, 120),
        calculate_harmonies(base_genesis, 240),
        calculate_harmonies(base_genesis, 240, val_mod=0.7)
    ]
elif harmony_rule == "Complementary":
    palette = [
        calculate_harmonies(base_genesis, 0, val_mod=0.5),
        calculate_harmonies(base_genesis, 0, val_mod=0.8),
        base_genesis,
        calculate_harmonies(base_genesis, 180),
        calculate_harmonies(base_genesis, 180, val_mod=0.6)
    ]
elif harmony_rule == "Split Complementary":
    palette = [
        calculate_harmonies(base_genesis, -150),
        calculate_harmonies(base_genesis, -30),
        base_genesis,
        calculate_harmonies(base_genesis, 150),
        calculate_harmonies(base_genesis, 180)
    ]
elif harmony_rule == "Square":
    palette = [
        base_genesis,
        calculate_harmonies(base_genesis, 90),
        calculate_harmonies(base_genesis, 180),
        calculate_harmonies(base_genesis, 270),
        calculate_harmonies(base_genesis, 270, val_mod=0.6)
    ]
elif harmony_rule == "Compound":
    palette = [
        calculate_harmonies(base_genesis, -30, sat_mod=0.6),
        calculate_harmonies(base_genesis, 30, val_mod=0.8),
        base_genesis,
        calculate_harmonies(base_genesis, 180, sat_mod=0.4),
        calculate_harmonies(base_genesis, 180)
    ]

# --- MAIN INTERFACE LAYOUT ---
col_wheel, col_values = st.columns([0.8, 1.4])

with col_wheel:
    st.write("### VDP 9-bit Color Wheel")
    fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw=dict(projection='polar'))
    
    ax.set_autoscale_on(False)
    ax.set_rmax(1.0)
    
    angles_bg = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    radii_bg = np.linspace(0.08, 1.0, 10)
    
    for a in angles_bg:
        for r_g in radii_bg:
            r_res, g_res, b_res = colorsys.hsv_to_rgb(a / (2 * np.pi), r_g, max(0.0, dynamic_value))
            q_r, q_g, q_b = quantize_to_genesis((int(r_res * 255), int(g_res * 255), int(b_res * 255)))
            ax.scatter(a, r_g, color=f"#{q_r:02X}{q_g:02X}{q_b:02X}", s=15, alpha=0.9, linewidths=0, zorder=1)
            
    for idx, color in enumerate(palette):
        r_v, g_v, b_v = int(color[0]), int(color[1]), int(color[2])
        r_n, g_n, b_n = r_v / 255.0, g_v / 255.0, b_v / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_n, g_n, b_n)
        rad_angle = h * 2 * np.pi
        s_plot = max(0.02, s)
        
        ax.plot([0, rad_angle], [0, s_plot], color="white", linestyle="--", alpha=0.8, linewidth=0.8, zorder=5)
        node_border = "#000000" if v > 0.5 else "#FFFFFF"
        
        ax.scatter(
            rad_angle, s_plot, 
            color=f"#{r_v:02X}{g_v:02X}{b_v:02X}", 
            edgecolor=node_border, s=100, zorder=10, linewidths=1.0
        )
        
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    st.pyplot(fig)
    
with col_values:
    st.write("### Calculated Harmonies")
    cols_palette = st.columns(5)
    
    for i, color in enumerate(palette):
        with cols_palette[i]:
            hex_color = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
            label_title = f"⭐ Base Color" if color == base_genesis and i == 2 else f"Color {i+1}"
            
            st.color_picker(label_title, hex_color, key=f"vdp_node_{i}_{hex_color.replace('#', '')}")
            st.markdown(f"**SGDK:** `{rgb_to_sgdk_hex(color)}`")
            st.caption(f"RGB: {color}")
            
            if st.button("➕ Add", key=f"add_btn_{i}_{hex_color.replace('#', '')}"):
                inserted = False
                for s_idx in range(16):
                    if st.session_state.custom_palette[s_idx] is None:
                        st.session_state.custom_palette[s_idx] = color
                        inserted = True
                        break
                if inserted:
                    st.rerun()
                else:
                    st.sidebar.error("All 16 slots are full!")

# --- 16-COLOR PALETTE BUILDER WORKSPACE ---
st.markdown("---")
st.write("### 🎛️ Active 16-Color Hardware Palette Builder")

active_colors = [c for c in st.session_state.custom_palette if c is not None]
st.caption(f"Slots filled: {len(active_colors)} / 16. (Use ◀ / ▶ arrows to organize index slots or ❌ to clear a single position).")

cols_16 = st.columns(16)
for i in range(16):
    with cols_16[i]:
        st.markdown(f"<center><b>Slot {i}</b></center>", unsafe_allow_html=True)
        slot_data = st.session_state.custom_palette[i]
        
        if slot_data is not None:
            slot_hex = f"#{slot_data[0]:02X}{slot_data[1]:02X}{slot_data[2]:02X}"
            st.color_picker(f"S{i}", slot_hex, key=f"slot_box_{i}_{slot_hex.replace('#','')}", label_visibility="collapsed")
            st.caption(f"<center><code>{rgb_to_sgdk_hex(slot_data)}</code></center>", unsafe_allow_html=True)
            
            move_left, clear_cell, move_right = st.columns(3)
            
            with move_left:
                if i > 0:
                    if st.button("◀", key=f"mv_l_{i}", help="Shift left"):
                        st.session_state.custom_palette[i-1], st.session_state.custom_palette[i] = st.session_state.custom_palette[i], st.session_state.custom_palette[i-1]
                        st.rerun()
                else:
                    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
            
            with clear_cell:
                if st.button("❌", key=f"clear_slot_btn_{i}", help="Delete color from this slot"):
                    st.session_state.custom_palette[i] = None
                    st.rerun()
                    
            with move_right:
                if i < 15:
                    if st.button("▶", key=f"mv_r_{i}", help="Shift right"):
                        st.session_state.custom_palette[i+1], st.session_state.custom_palette[i] = st.session_state.custom_palette[i], st.session_state.custom_palette[i+1]
                        st.rerun()
                else:
                    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        else:
            st.color_picker(f"S{i}", "#222222", key=f"slot_box_empty_{i}", disabled=True, label_visibility="collapsed")
            st.caption("<center><code style='color:gray;'>0x----</code></center>", unsafe_allow_html=True)
            st.markdown("<br><br><br>", unsafe_allow_html=True)

if any(c is not None for c in st.session_state.custom_palette):
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Clear Full Palette Work-area", type="secondary"):
        st.session_state.custom_palette = [None] * 16
        st.rerun()

# --- CODE EXPORT & ASEPRITE DOWNLOAD BLOCK ---
if any(c is not None for c in st.session_state.custom_palette):
    st.markdown("---")
    st.write("### 💻 Export Code & Assets for Your Project")
    st.caption("These assets update dynamically containing only the active valid colors from your 16 slots.")
    
    gpl_content = "GIMP Palette\nName: Sega Genesis Custom Palette\nColumns: 16\n#\n"
    for idx, c in enumerate(st.session_state.custom_palette):
        if c is not None:
            gpl_content += f"{c[0]:3d} {c[1]:3d} {c[2]:3d}\t{rgb_to_sgdk_hex(c)}\n"
        else:
            gpl_content += f" 34  34  34\tEmpty_Slot_{idx}\n"
            
    st.download_button(
        label="📥 Download Palette for Aseprite (.GPL)",
        data=gpl_content,
        file_name="genesis_palette.gpl",
        mime="text/plain",
        type="primary"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    tab_sgdk, tab_asm, tab_raw = st.tabs(["SGDK (C Array)", "Assembly (68k)", "Decimal Values"])
    
    with tab_sgdk:
        hex_strings = [rgb_to_sgdk_hex(c) for c in st.session_state.custom_palette if c is not None]
        sgdk_code = f"// Custom Sega Genesis Palette Block\nconst u16 custom_vdp_palette[{len(hex_strings)}] = {{\n    {', '.join(hex_strings)}\n}};"
        st.code(sgdk_code, language="c")
        
    with tab_asm:
        asm_strings = [rgb_to_asm_hex(c) for c in st.session_state.custom_palette if c is not None]
        asm_code = f"; Custom Sega Genesis Palette Block\nCustomVDPPalette:\n    dc.w {', '.join(asm_strings)}"
        st.code(asm_code, language="asm")
        
    with tab_raw:
        st.text("Raw RGB Tuple List Layout:")
        for idx, c in enumerate(st.session_state.custom_palette):
            if c is not None:
                st.text(f"Slot {idx}: {c}")
else:
    st.markdown("---")
    st.info("💡 Add colors using the **➕ Add** buttons under the calculated harmonies to populate your 16-color workspace and unlock the export panel.")

# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("Sega Genesis / Mega Drive Color Wheel | Conceptualized & Tested by Rodrigo Fontanella | Code co-generated via AI Assist | Open-source community tool.")
