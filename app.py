import streamlit as st
import colorsys
import matplotlib.pyplot as plt
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sega Genesis / Mega Drive Color Wheel", page_icon="🎮", layout="wide")

st.title("🎮 Sega Genesis / Mega Drive Color Wheel")
st.markdown("Create and calculate color harmonies locked strictly to the **512 colors (9-bit VDP RGB)** of the original hardware.")

# --- INJECT CUSTOM CSS FOR PERFECT GLOBAL ALIGNMENT AND SYMMETRY ---
st.markdown("""
    <style>
        /* Disable mouse selection events on disabled/preview color picks */
        div[data-testid="stColorPicker"] {
            pointer-events: none !important;
            cursor: default !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stColorPicker"] {
            pointer-events: auto !important;
        }
        
        /* FIX 1: Force absolute horizontal centralization on ALL components inside layout columns */
        div[data-testid="column"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
            justify-content: flex-start !important;
            width: 100% !important;
        }
        
        /* FIX 2: Ensure color picker blocks maintain 100% width but center their internal color square */
        div[data-testid="stColorPicker"], div[data-testid="stColorPickerBlock"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0 auto !important;
            width: 100% !important;
        }
        div[data-testid="stColorPicker"] > div {
            margin: 0 auto !important;
            width: 44px !important;
        }
        
        /* FIX 3: Force 'Add' and wrapper button divs to align to the absolute center of their grids */
        div.stButton, div[data-testid="stHorizontalBlock"] div.stButton, .stButton {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0 auto !important;
            width: 100% !important;
        }
        
        /* FIX 4: Reset markdown and caption elements to align text natively in the center */
        div[data-testid="stMarkdown"], div[data-testid="stCaptionBlock"], p, center, b, code {
            display: block !important;
            text-align: center !important;
            width: 100% !important;
            margin: 0 auto !important;
        }
        
        /* Force uniform line height and design footprint on all slot controls */
        div[data-testid="stHorizontalBlock"] button, div.stButton > button {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 auto !important;
            padding: 2px 0px !important;
            height: 28px !important;
            width: 100% !important;
            text-align: center !important;
            line-height: 1 !important;
        }
        
        /* Eliminate unexpected layout padding issues */
        div[data-testid="column"] [data-testid="stHorizontalBlock"] {
            gap: 2px !important;
            width: 100% !important;
        }
        div[data-testid="column"] [data-testid="stHorizontalBlock"] div[data-testid="column"] {
            padding: 0px 1px !important;
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

# --- FIXED ULTRA PERFORMANCE ENGINE: Pre-calculating arrays into single memory blocks ---
@st.cache_data
def get_cached_precomputed_wheel(brightness_val):
    angles = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    radii = np.linspace(0.08, 1.0, 10)
    
    a_list, r_list, c_list = [], [], []
    for a in angles:
        for r_g in radii:
            r_res, g_res, b_res = colorsys.hsv_to_rgb(a / (2 * np.pi), r_g, max(0.0, brightness_val))
            q_r, q_g, q_b = quantize_to_genesis((int(r_res * 255), int(g_res * 255), int(b_res * 255)))
            a_list.append(a)
            r_list.append(r_g)
            c_list.append(f"#{q_r:02X}{q_g:02X}{q_b:02X}")
            
    return np.array(a_list), np.array(r_list), c_list


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

r_hex_val = int(base_genesis[0])
g_hex_val = int(base_genesis[1])
b_hex_val = int(base_genesis[2])
base_hex = f"#{r_hex_val:02X}{g_hex_val:02X}{b_hex_val:02X}"

st.sidebar.markdown("**Selected Base Preview:**")
st.sidebar.markdown(f"""
    <div style="display:flex; justify-content:center; align-items:center; width:100%; margin: 5px 0;">
        <div style="width:50px; height:30px; background-color:{base_hex}; border-radius:4px; border:2px solid #555; box-shadow:0px 2px 4px rgba(0,0,0,0.3);"></div>
    </div>
""", unsafe_allow_html=True)

# --- IMPORT ASEPRITE .GPL PALETTE ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Import Palette (.GPL)")
uploaded_gpl = st.sidebar.file_uploader("Upload an Aseprite GPL file:", type=["gpl"])

if uploaded_gpl is not None:
    try:
        gpl_lines = uploaded_gpl.read().decode("utf-8").splitlines()
        imported_colors = []
        for line in gpl_lines:
            line = line.strip()
            if not line or line.startswith("GIMP") or line.startswith("Name:") or line.startswith("Columns:") or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    r_imp = int(parts[0])
                    g_imp = int(parts[1])
                    b_imp = int(parts[2])
                    imported_colors.append(quantize_to_genesis((r_imp, g_imp, b_imp)))
                except ValueError:
                    continue
        new_palette = [None] * 16
        for idx, col in enumerate(imported_colors[:16]):
            if col == (34, 34, 34):
                new_palette[idx] = None
            else:
                new_palette[idx] = col
        st.session_state.custom_palette = new_palette
        st.sidebar.success(f"Successfully loaded {len(imported_colors[:16])} indices!")
    except Exception as e:
        st.sidebar.error("Error reading GPL file.")

# Extract active hardware brightness
r_norm, g_norm, b_norm = base_genesis[0]/255.0, base_genesis[1]/255.0, base_genesis[2]/255.0
_, _, dynamic_value = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)

# --- HARMONY RULE LOGIC ---
palette = []
if harmony_rule == "Analogous":
    palette = [calculate_harmonies(base_genesis, -60), calculate_harmonies(base_genesis, -30), base_genesis, calculate_harmonies(base_genesis, 30), calculate_harmonies(base_genesis, 60)]
elif harmony_rule == "Monochromatic":
    palette = [calculate_harmonies(base_genesis, 0, sat_mod=0.2, val_mod=0.4), calculate_harmonies(base_genesis, 0, sat_mod=0.5, val_mod=0.7), base_genesis, calculate_harmonies(base_genesis, 0, sat_mod=0.8, val_mod=0.9), calculate_harmonies(base_genesis, 0, sat_mod=0.6, val_mod=1.2)]
elif harmony_rule == "Triad":
    palette = [calculate_harmonies(base_genesis, 0, val_mod=0.6), base_genesis, calculate_harmonies(base_genesis, 120), calculate_harmonies(base_genesis, 240), calculate_harmonies(base_genesis, 240, val_mod=0.7)]
elif harmony_rule == "Complementary":
    palette = [calculate_harmonies(base_genesis, 0, val_mod=0.5), calculate_harmonies(base_genesis, 0, val_mod=0.8), base_genesis, calculate_harmonies(base_genesis, 180), calculate_harmonies(base_genesis, 180, val_mod=0.6)]
elif harmony_rule == "Split Complementary":
    palette = [calculate_harmonies(base_genesis, -150), calculate_harmonies(base_genesis, -30), base_genesis, calculate_harmonies(base_genesis, 150), calculate_harmonies(base_genesis, 180)]
elif harmony_rule == "Square":
    palette = [base_genesis, calculate_harmonies(base_genesis, 90), calculate_harmonies(base_genesis, 180), calculate_harmonies(base_genesis, 270), calculate_harmonies(base_genesis, 270, val_mod=0.6)]
elif harmony_rule == "Compound":
    palette = [calculate_harmonies(base_genesis, -30, sat_mod=0.6), calculate_harmonies(base_genesis, 30, val_mod=0.8), base_genesis, calculate_harmonies(base_genesis, 180, sat_mod=0.4), calculate_harmonies(base_genesis, 180)]

# --- MAIN INTERFACE LAYOUT ---
col_wheel, col_values = st.columns([0.8, 1.4])

with col_wheel:
    st.write("### VDP 9-bit Color Wheel")
    fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw=dict(projection='polar'))
    
    ax.set_autoscale_on(False)
    ax.set_rmax(1.12)
    
    # ⚡ VETORIAL INJECTION: Draws 640 dots in ONE single microsecond operation instead of a heavy loop!
    bg_a, bg_r, bg_c = get_cached_precomputed_wheel(dynamic_value)
    ax.scatter(bg_a, bg_r, color=bg_c, s=15, alpha=0.9, linewidths=0, zorder=1)
            
    for idx, color in enumerate(palette):
        r_v, g_v, b_v = int(color[0]), int(color[1]), int(color[2])
        r_n, g_n, b_n = r_v / 255.0, g_v / 255.0, b_v / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_n, g_n, b_n)
        rad_angle = h * 2 * np.pi
        s_plot = max(0.02, s)
        
        ax.plot([0, rad_angle], [0, s_plot], color="white", linestyle="--", alpha=0.8, linewidth=0.8, zorder=5)
        node_border = "#000000" if v > 0.5 else "#FFFFFF"
        ax.scatter(rad_angle, s_plot, color=f"#{r_v:02X}{g_v:02X}{b_v:02X}", edgecolor=node_border, s=100, zorder=10, linewidths=1.0)
        
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    
    # Render graphic canvas
    st.pyplot(fig)
    
    # 🛑 MEMORY LEAK FIX: Force closes the active plot immediately to clear server cache.
    # This prevents the dots from compounding over time and fixes the giant-circle bug!
    plt.close(fig)


with col_values:
    st.write("### Calculated Harmonies")
    cols_palette = st.columns(5)
    
    display_count = min(len(palette), 5)
    for i in range(display_count):
        color = palette[i]
        with cols_palette[i]:
            with st.container():
                r_c, g_c, b_c = int(color[0]), int(color[1]), int(color[2])
                hex_color = f"#{r_c:02X}{g_c:02X}{b_c:02X}"
                label_title = f"⭐ Base" if color == base_genesis and i == 2 else f"Color {i+1}"
                
                st.markdown(f"""
                    <div style="display:flex; flex-direction:column; align-items:center; width:100%; text-align:center;">
                        <div style="font-weight:bold; font-size:14px; margin-bottom:5px;">{label_title}</div>
                        <div style="width:44px; height:44px; background-color:{hex_color}; border-radius:4px; border:2px solid #555; box-shadow:0px 2px 4px rgba(0,0,0,0.25); margin-bottom:6px;"></div>
                        <div style="margin-bottom:2px;"><code>{rgb_to_sgdk_hex(color)}</code></div>
                        <div style="color:gray; font-size:11px; margin-bottom:8px;">({r_c},{g_c},{b_c})</div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_l, col_btn_mid, col_btn_r = st.columns(3)
                with col_btn_mid:
                    if st.button("➕", key=f"add_btn_{i}_{hex_color.replace('#', '')}"):
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

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    if not any(c is not None for c in st.session_state.custom_palette):
        st.info("💡 Add colors using the **➕** buttons above to populate your 16-color workspace and unlock the export generator panel below.")
    else:
        st.success("💡 Colors added successfully! Organize your sequence below using the arrow controls.")

# --- 16-COLOR PALETTE BUILDER WORKSPACE ---
st.markdown("---")
st.write("### 🎛️ Active 16-Color Hardware Palette Builder")

active_colors = [c for c in st.session_state.custom_palette if c is not None]
st.caption(f"Slots filled: {len(active_colors)} / 16. (Use ◀ / ▶ arrows to organize index slots or X to clear a single position).")

cols_16 = st.columns(16)
for i in range(16):
    with cols_16[i]:
        st.markdown(f"<center><b>Slot {i}</b></center>", unsafe_allow_html=True)
        slot_data = st.session_state.custom_palette[i]
        
        if slot_data is not None:
            with st.container():
                r_sl, g_sl, b_sl = int(slot_data[0]), int(slot_data[1]), int(slot_data[2])
                slot_hex = f"#{r_sl:02X}{g_sl:02X}{b_sl:02X}"
                
                st.markdown(f"""
                    <div style="display:flex; flex-direction:column; align-items:center; width:100%; text-align:center; margin-bottom:5px;">
                        <div style="width:40px; height:44px; background-color:{slot_hex}; border-radius:4px; border:2px solid #555; box-shadow:0px 2px 4px rgba(0,0,0,0.2); margin-bottom:4px;"></div>
                        <code>{rgb_to_sgdk_hex(slot_data)}</code>
                    </div>
                """, unsafe_allow_html=True)
                
                move_left, clear_cell, move_right = st.columns(3)
                
                with move_left:
                    if i > 0:
                        if st.button("◀", key=f"mv_l_{i}", help="Shift left"):
                            st.session_state.custom_palette[i-1], st.session_state.custom_palette[i] = st.session_state.custom_palette[i], st.session_state.custom_palette[i-1]
                            st.rerun()
                    else:
                        st.markdown("<div style='height:28px; width:100%; visibility:hidden;'></div>", unsafe_allow_html=True)
                
                with clear_cell:
                    if st.button("X", key=f"clear_slot_btn_{i}", help="Delete color from this slot"):
                        st.session_state.custom_palette[i] = None
                        st.rerun()
                        
                with move_right:
                    if i < 15:
                        if st.button("▶", key=f"mv_r_{i}", help="Shift right"):
                            st.session_state.custom_palette[i+1], st.session_state.custom_palette[i] = st.session_state.custom_palette[i], st.session_state.custom_palette[i+1]
                            st.rerun()
                    else:
                        st.markdown("<div style='height:28px; width:100%; visibility:hidden;'></div>", unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown("""
                    <div style="display:flex; flex-direction:column; align-items:center; width:100%; text-align:center; margin-bottom:5px;">
                        <div style="width:40px; height:44px; background-color:#222; border-radius:4px; border:2px dashed #44px; margin-bottom:4px;"></div>
                        <code style="color:gray;">0x----</code>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<br><br><br>", unsafe_allow_html=True)


if any(c is not None for c in st.session_state.custom_palette):
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Clear Full Palette Work-area", type="secondary"):
        st.session_state.custom_palette = [None] * 16
        st.rerun()

# --- CODE EXPORT & ASEPRITE DOWNLOAD BLOCK ---
if [c for c in st.session_state.custom_palette if c is not None]:
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
                st.text(f"Slot {idx}: ({c[0]}, {c[1]}, {c[2]})")

# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("Sega Genesis / Mega Drive Color Wheel | Conceptualized & Tested by Rodrigo Fontanella | Code co-generated via AI Assist | Open-source community tool.")
