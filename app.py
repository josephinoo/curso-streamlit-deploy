
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Netflix Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════
# HELPERS DE PLOTLY — estilo oscuro reutilizable
# ══════════════════════════════════════════════════════════════
LAYOUT_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cccccc", family="Inter, sans-serif"),
    margin=dict(t=50, b=20, l=10, r=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#888"),
    ),
    xaxis=dict(gridcolor="#222", zeroline=False),
    yaxis=dict(gridcolor="#222", zeroline=False),
)

COLORS = {
    "Movie":    "#e50914",
    "TV Show":  "#b20710",
    "seq":      "Reds",
    "accent":   "#e50914",
    "muted":    "#555555",
}


# ══════════════════════════════════════════════════════════════
# SESSION STATE — inicializar estado global
# ══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "tipo":        "Todos",
        "pais":        "Todos",
        "anio_rango":  (2000, 2021),
        "titulo_sel":  None,
        "dialog_open": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════
# CARGA Y TRANSFORMACIÓN DEL DATASET
# ══════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def cargar_netflix(ruta: str) -> pd.DataFrame:
    """Carga y transforma el dataset de Netflix."""
    df = pd.read_csv(ruta)

    # Fechas
    df["date_added"]     = pd.to_datetime(df["date_added"].str.strip(), errors="coerce")
    df["anio_agregado"]  = df["date_added"].dt.year.astype("Int64")
    df["mes_agregado"]   = df["date_added"].dt.month_name()

    # País principal (el primero de la lista)
    df["pais_principal"] = df["country"].str.split(",").str[0].str.strip()

    # Duración numérica
    df["duracion_num"] = (
        df["duration"]
        .str.extract(r"(\d+)")[0]
        .astype(float)
    )

    # Limpieza de texto
    df["director"] = df["director"].fillna("Sin datos")
    df["cast"]     = df["cast"].fillna("Sin datos")
    df["country"]  = df["country"].fillna("Sin datos")
    df["listed_in"]= df["listed_in"].fillna("Sin datos")

    return df


# ══════════════════════════════════════════════════════════════
# DIALOG — detalle de un título
# ══════════════════════════════════════════════════════════════
@st.dialog("Detalle del título", width="large")
def mostrar_detalle(titulo: str, df: pd.DataFrame):
    mask = df["title"] == titulo
    if not mask.any():
        st.error("Título no encontrado")
        return

    fila = df[mask].iloc[0]

    # Cabecera
    col_badge, col_title = st.columns([1, 5])
    badge_color = "#e50914" if fila["type"] == "Movie" else "#b20710"
    col_badge.markdown(
        f'<span style="background:{badge_color};color:white;padding:4px 10px;'
        f'border-radius:4px;font-size:0.7em;font-weight:700;">'
        f'{fila["type"]}</span>',
        unsafe_allow_html=True,
    )
    col_title.subheader(fila["title"])

    st.caption(
        f"**{fila['release_year']}**  ·  {fila['rating']}  ·  {fila['duration']}"
    )
    st.write(fila["description"])
    st.divider()

    c1, c2 = st.columns(2)
    c1.write(f"**Director:** {fila['director']}")
    c1.write(f"**País:** {fila['country']}")
    c2.write(f"**Géneros:** {fila['listed_in']}")
    c2.write(f"**Reparto:** {fila['cast'][:80]}..." if len(str(fila["cast"])) > 80 else f"**Reparto:** {fila['cast']}")

    if pd.notna(fila["date_added"]):
        st.caption(f"Agregado a Netflix: {fila['date_added'].strftime('%d %B %Y')}")


# ══════════════════════════════════════════════════════════════
# CARGA CON PROGRESS BAR
# ══════════════════════════════════════════════════════════════
loading_placeholder = st.empty()

with loading_placeholder.container():
    barra = st.progress(0, text="Cargando catálogo Netflix...")
    for i, msg in enumerate([
        "Leyendo archivo CSV...",
        "Procesando fechas...",
        "Calculando métricas...",
        "Preparando visualizaciones...",
    ]):
        barra.progress((i + 1) * 25, text=msg)
        time.sleep(0.15)

try:
    df_raw = cargar_netflix("netflix_titles.csv")
    loading_placeholder.empty()
except FileNotFoundError:
    loading_placeholder.empty()
    st.error(
        "**Archivo no encontrado.** Descarga `netflix_titles.csv` de "
        "[Kaggle](https://www.kaggle.com/datasets/shivamb/netflix-shows) "
        "y ponlo en la misma carpeta que este script."
    )
    st.stop()


# ══════════════════════════════════════════════════════════════
# SIDEBAR — logo + filtros
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo Netflix en texto (no necesita imagen externa)
    st.markdown(
        '<h1 style="color:#e50914;font-size:2.2rem;font-weight:900;'
        'letter-spacing:-0.04em;margin-bottom:0;">NETFLIX</h1>'
        '<p style="color:#666;font-size:0.65rem;margin-top:0;'
        'text-transform:uppercase;letter-spacing:0.1em;">Dashboard · 2025</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Tipo de contenido ─────────────────────────────────────
    st.caption("TIPO DE CONTENIDO")
    tipo = st.radio(
        "Tipo",
        ["Todos", "Movie", "TV Show"],
        key="tipo",
        label_visibility="collapsed",
        horizontal=True,
    )

    st.divider()

    # ── Año de lanzamiento ────────────────────────────────────
    st.caption("AÑO DE LANZAMIENTO")
    anio_rango = st.slider(
        "Año",
        min_value=1925,
        max_value=2021,
        value=st.session_state.anio_rango,
        key="anio_rango",
        label_visibility="collapsed",
    )

    st.divider()

    # ── País ──────────────────────────────────────────────────
    st.caption("PAÍS PRINCIPAL")
    paises_disponibles = sorted(
        df_raw["pais_principal"].dropna().unique().tolist()
    )
    pais = st.selectbox(
        "País",
        ["Todos"] + paises_disponibles,
        key="pais",
        label_visibility="collapsed",
    )

    st.divider()

    # ── Filtros avanzados (popover) ───────────────────────────
    with st.popover("Filtros avanzados", use_container_width=True):
        ratings_disp = sorted(df_raw["rating"].dropna().unique().tolist())
        ratings_sel = st.multiselect("Rating:", ratings_disp, default=ratings_disp[:])

        generos_todos = sorted(
            df_raw["listed_in"]
            .dropna()
            .str.split(", ")
            .explode()
            .unique()
            .tolist()
        )
        genero_sel = st.selectbox("Género:", ["Todos"] + generos_todos)

    st.divider()

    # Botón de reset
    if st.button("Restablecer filtros", use_container_width=True):
        for k in ["tipo", "pais", "anio_rango"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


# ══════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ══════════════════════════════════════════════════════════════
df = df_raw.copy()

if tipo != "Todos":
    df = df[df["type"] == tipo]

if pais != "Todos":
    df = df[df["pais_principal"] == pais]

df = df[
    df["release_year"].between(anio_rango[0], anio_rango[1])
]

if "ratings_sel" in dir() and ratings_sel:
    df = df[df["rating"].isin(ratings_sel)]

if "genero_sel" in dir() and genero_sel != "Todos":
    df = df[df["listed_in"].str.contains(genero_sel, na=False)]


# ══════════════════════════════════════════════════════════════
# KPIs PRINCIPALES
# ══════════════════════════════════════════════════════════════
total      = len(df)
n_peliculas= int((df["type"] == "Movie").sum())
n_series   = int((df["type"] == "TV Show").sum())
n_paises   = int(df["pais_principal"].nunique())
n_dirs     = int(df[df["director"] != "Sin datos"]["director"].nunique())
pct_movies = f"{n_peliculas/total*100:.0f}% del total" if total else "—"
pct_series = f"{n_series/total*100:.0f}% del total" if total else "—"

# Cabecera
st.markdown(
    '<h1 style="font-size:2rem;font-weight:900;letter-spacing:-0.03em;'
    'margin-bottom:0.1em;">Catálogo Netflix</h1>'
    '<p style="color:#666;font-size:0.8rem;margin-top:0;">'
    'Análisis interactivo · 1925 – 2021</p>',
    unsafe_allow_html=True,
)

# Panel de KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total títulos",   f"{total:,}")
k2.metric("Películas",       f"{n_peliculas:,}",   pct_movies)
k3.metric("Series",          f"{n_series:,}",      pct_series)
k4.metric("Países",          f"{n_paises:,}")
k5.metric("Directores",      f"{n_dirs:,}")

st.divider()


# ══════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ══════════════════════════════════════════════════════════════
if total == 0:
    st.warning("No hay datos con los filtros seleccionados. Ajusta los filtros del sidebar.")
    st.stop()

t_overview, t_peliculas, t_series, t_directores, t_paises = st.tabs([
    "Overview",
    "Peliculas",
    "Series",
    "Directores",
    "Paises",
])


# ──────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ──────────────────────────────────────────────────────────────
with t_overview:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Timeline de contenido agregado
        df_timeline = (
            df.dropna(subset=["anio_agregado"])
              .groupby(["anio_agregado", "type"], as_index=False)
              .size()
              .rename(columns={"size": "count"})
        )
        fig_timeline = px.bar(
            df_timeline,
            x="anio_agregado",
            y="count",
            color="type",
            title="Títulos agregados al catálogo por año",
            labels={"anio_agregado": "Año", "count": "Títulos", "type": ""},
            color_discrete_map=COLORS,
            barmode="stack",
        )
        fig_timeline.update_layout(**LAYOUT_BASE, showlegend=True)
        fig_timeline.update_layout(legend=dict(orientation="h", y=1.1))
        fig_timeline.update_traces(
            hovertemplate="<b>%{x}</b><br>%{y} títulos<extra></extra>"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_right:
        # Donut Movie vs TV Show
        df_tipo = df.groupby("type", as_index=False).size()
        fig_donut = px.pie(
            df_tipo,
            names="type",
            values="size",
            title="Distribución del catálogo",
            hole=0.60,
            color="type",
            color_discrete_map=COLORS,
        )
        fig_donut.update_traces(
            textinfo="percent+label",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>%{value:,} títulos<br>%{percent}<extra></extra>",
        )
        fig_donut.update_layout(**LAYOUT_BASE, showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Tabla con buscador
    st.subheader("Explorar títulos")

    col_search, col_popover, _ = st.columns([3, 1, 3])

    with col_search:
        busqueda = st.text_input(
            "Buscar",
            placeholder="Buscar título...",
            label_visibility="collapsed",
        )

    df_tabla = df.copy()
    if busqueda:
        df_tabla = df_tabla[
            df_tabla["title"].str.contains(busqueda, case=False, na=False)
        ]

    # Selección de título para el dialog
    titulo_opciones = df_tabla["title"].dropna().tolist()

    col_sel, col_btn = st.columns([4, 1])
    titulo_elegido = col_sel.selectbox(
        "Título",
        titulo_opciones if titulo_opciones else ["(sin resultados)"],
        label_visibility="collapsed",
    )
    if col_btn.button("Ver detalle", type="primary",
                      disabled=(not titulo_opciones)):
        mostrar_detalle(titulo_elegido, df)

    st.dataframe(
        df_tabla[["title", "type", "release_year", "country",
                  "listed_in", "rating", "duration", "date_added"]].head(300),
        use_container_width=True,
        hide_index=True,
        height=380,
        column_config={
            "title":        st.column_config.TextColumn("Título", width="large"),
            "type":         st.column_config.TextColumn("Tipo", width="small"),
            "release_year": st.column_config.NumberColumn("Año", format="%d", width="small"),
            "country":      st.column_config.TextColumn("País"),
            "listed_in":    st.column_config.TextColumn("Géneros", width="large"),
            "rating":       st.column_config.TextColumn("Rating", width="small"),
            "duration":     st.column_config.TextColumn("Duración", width="small"),
            "date_added":   st.column_config.DateColumn("Agregado", format="DD/MM/YYYY"),
        },
    )


# ──────────────────────────────────────────────────────────────
# TAB 2 — PELÍCULAS
# ──────────────────────────────────────────────────────────────
with t_peliculas:
    df_movies = df[df["type"] == "Movie"]

    if df_movies.empty:
        st.info("No hay películas con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            # Top géneros películas
            gen_movies = (
                df_movies["listed_in"]
                .dropna()
                .str.split(", ")
                .explode()
                .value_counts()
                .head(15)
                .reset_index()
            )
            gen_movies.columns = ["genero", "count"]

            fig_gen_m = px.bar(
                gen_movies,
                x="count", y="genero", orientation="h",
                title="Top 15 géneros — Películas",
                labels={"count": "Títulos", "genero": ""},
                color="count",
                color_continuous_scale=COLORS["seq"],
            )
            fig_gen_m.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
            fig_gen_m.update_layout(yaxis=dict(categoryorder="total ascending", gridcolor="#222"))
            st.plotly_chart(fig_gen_m, use_container_width=True)

        with col2:
            # Distribución de duración
            df_dur = df_movies.dropna(subset=["duracion_num"])
            fig_dur = px.histogram(
                df_dur,
                x="duracion_num",
                nbins=40,
                title="Distribución de duración (minutos)",
                labels={"duracion_num": "Minutos", "count": "Películas"},
                color_discrete_sequence=[COLORS["accent"]],
            )
            fig_dur.update_layout(**LAYOUT_BASE)
            fig_dur.update_traces(
                hovertemplate="<b>%{x} min</b><br>%{y} películas<extra></extra>"
            )
            st.plotly_chart(fig_dur, use_container_width=True)

        # Películas por año de lanzamiento
        df_m_anio = (
            df_movies.groupby("release_year", as_index=False)
                     .size()
                     .rename(columns={"size": "count"})
        )
        fig_m_anio = px.area(
            df_m_anio,
            x="release_year", y="count",
            title="Películas por año de lanzamiento",
            labels={"release_year": "Año", "count": "Películas"},
            color_discrete_sequence=[COLORS["accent"]],
        )
        fig_m_anio.update_traces(
            fill="tozeroy",
            fillcolor="rgba(229,9,20,0.12)",
            line=dict(color=COLORS["accent"], width=2),
        )
        fig_m_anio.update_layout(**LAYOUT_BASE)
        st.plotly_chart(fig_m_anio, use_container_width=True)

        # Stats rápidas
        with st.expander("Estadísticas de duración"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Duración promedio",  f"{df_movies['duracion_num'].mean():.0f} min")
            c2.metric("Más larga",          f"{df_movies['duracion_num'].max():.0f} min")
            c3.metric("Más corta",          f"{df_movies['duracion_num'].min():.0f} min")
            c4.metric("Mediana",            f"{df_movies['duracion_num'].median():.0f} min")


# ──────────────────────────────────────────────────────────────
# TAB 3 — SERIES
# ──────────────────────────────────────────────────────────────
with t_series:
    df_shows = df[df["type"] == "TV Show"]

    if df_shows.empty:
        st.info("No hay series con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            # Distribución de temporadas
            df_temp = df_shows.dropna(subset=["duracion_num"])
            fig_temp = px.bar(
                df_temp["duracion_num"]
                       .value_counts()
                       .sort_index()
                       .reset_index()
                       .rename(columns={"duracion_num": "temporadas",
                                        "count": "series"}),
                x="temporadas", y="series",
                title="Series por número de temporadas",
                labels={"temporadas": "Temporadas", "series": "Series"},
                color="series",
                color_continuous_scale=COLORS["seq"],
            )
            fig_temp.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
            st.plotly_chart(fig_temp, use_container_width=True)

        with col2:
            # Top géneros series
            gen_shows = (
                df_shows["listed_in"]
                .dropna()
                .str.split(", ")
                .explode()
                .value_counts()
                .head(12)
                .reset_index()
            )
            gen_shows.columns = ["genero", "count"]

            fig_gen_s = px.bar(
                gen_shows,
                x="count", y="genero", orientation="h",
                title="Top géneros — Series",
                labels={"count": "Series", "genero": ""},
                color="count",
                color_continuous_scale=COLORS["seq"],
            )
            fig_gen_s.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
            fig_gen_s.update_layout(yaxis=dict(categoryorder="total ascending", gridcolor="#222"))
            st.plotly_chart(fig_gen_s, use_container_width=True)

        # Distribución de ratings
        df_rating = (
            df_shows.groupby("rating", as_index=False)
                    .size()
                    .sort_values("size", ascending=False)
        )
        fig_rating = px.bar(
            df_rating,
            x="rating", y="size",
            title="Series por clasificación de contenido (Rating)",
            labels={"rating": "Rating", "size": "Series"},
            color="size",
            color_continuous_scale=COLORS["seq"],
        )
        fig_rating.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
        st.plotly_chart(fig_rating, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# TAB 4 — DIRECTORES
# ──────────────────────────────────────────────────────────────
with t_directores:
    df_dirs = df[df["director"] != "Sin datos"]

    if df_dirs.empty:
        st.info("No hay directores con los filtros actuales.")
    else:
        col1, col2 = st.columns([2, 3])

        with col1:
            # Top directores
            top_dirs = (
                df_dirs.groupby("director", as_index=False)
                       .agg(
                           titulos=("show_id", "count"),
                           peliculas=("type", lambda x: (x == "Movie").sum()),
                           series=("type", lambda x: (x == "TV Show").sum()),
                       )
                       .sort_values("titulos", ascending=False)
                       .head(20)
            )

            st.subheader("Top 20 directores")
            st.dataframe(
                top_dirs,
                use_container_width=True,
                hide_index=True,
                height=500,
                column_config={
                    "director": st.column_config.TextColumn("Director"),
                    "titulos":  st.column_config.ProgressColumn(
                                    "Títulos",
                                    min_value=0,
                                    max_value=int(top_dirs["titulos"].max()),
                                    format="%d"),
                    "peliculas":st.column_config.NumberColumn("Películas"),
                    "series":   st.column_config.NumberColumn("Series"),
                },
            )

        with col2:
            fig_dir = px.bar(
                top_dirs.head(15),
                x="titulos", y="director",
                orientation="h",
                title="Top 15 directores por número de títulos",
                labels={"titulos": "Títulos", "director": ""},
                color="titulos",
                color_continuous_scale=COLORS["seq"],
                text="titulos",
            )
            fig_dir.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
            fig_dir.update_layout(yaxis=dict(categoryorder="total ascending", gridcolor="#222"))
            fig_dir.update_traces(
                textposition="outside",
                textfont=dict(color="#ccc"),
            )
            st.plotly_chart(fig_dir, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# TAB 5 — PAÍSES (MAPA CHOROPLETH)
# ──────────────────────────────────────────────────────────────
with t_paises:

    df_paises = (
        df[df["pais_principal"] != "Sin datos"]
          .groupby("pais_principal", as_index=False)
          .agg(titulos=("show_id", "count"))
          .sort_values("titulos", ascending=False)
    )

    # Intentar importar pycountry para convertir nombres a ISO-3
    try:
        import pycountry

        @st.cache_data
        def nombre_a_iso3(nombre: str) -> str | None:
            try:
                return pycountry.countries.search_fuzzy(nombre)[0].alpha_3
            except Exception:
                return None

        df_paises["iso_alpha"] = df_paises["pais_principal"].apply(nombre_a_iso3)
        df_paises_map = df_paises.dropna(subset=["iso_alpha"])
        usar_mapa = True

    except ImportError:
        usar_mapa = False

    if usar_mapa and not df_paises_map.empty:
        fig_mapa = px.choropleth(
            df_paises_map,
            locations="iso_alpha",
            color="titulos",
            hover_name="pais_principal",
            hover_data={"titulos": True, "iso_alpha": False},
            color_continuous_scale="Reds",
            title="Distribución global del catálogo Netflix",
            labels={"titulos": "Títulos"},
        )
        fig_mapa.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor="#333",
                bgcolor="rgba(0,0,0,0)",
                showland=True,
                landcolor="#1a1a1a",
                showocean=True,
                oceancolor="#0d0d0d",
                showlakes=False,
                projection=dict(type="natural earth"),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc"),
            coloraxis_colorbar=dict(
                title=dict(text="Títulos", font=dict(color="#888")),
                tickfont=dict(color="#888"),
                bgcolor="rgba(0,0,0,0)",
                outlinecolor="#333",
            ),
            margin=dict(t=50, b=0, l=0, r=0),
            height=500,
        )
        st.plotly_chart(fig_mapa, use_container_width=True)

    else:
        st.info(
            "Instala `pycountry` para activar el mapa: `pip install pycountry`\n\n"
            "Mostrando tabla en su lugar:"
        )

    # Siempre mostrar tabla de países
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Top 20 países")
        st.dataframe(
            df_paises.head(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "pais_principal": st.column_config.TextColumn("País"),
                "titulos": st.column_config.ProgressColumn(
                    "Títulos",
                    min_value=0,
                    max_value=int(df_paises["titulos"].max()),
                    format="%d",
                ),
            },
        )

    with col2:
        fig_paises_bar = px.bar(
            df_paises.head(15),
            x="titulos", y="pais_principal",
            orientation="h",
            title="Top 15 países por número de títulos",
            labels={"titulos": "Títulos", "pais_principal": ""},
            color="titulos",
            color_continuous_scale=COLORS["seq"],
            text="titulos",
        )
        fig_paises_bar.update_layout(**LAYOUT_BASE, coloraxis_showscale=False)
        fig_paises_bar.update_layout(yaxis=dict(categoryorder="total ascending", gridcolor="#222"))
        fig_paises_bar.update_traces(
            textposition="outside",
            textfont=dict(color="#ccc"),
        )
        st.plotly_chart(fig_paises_bar, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "Dashboard construido con Streamlit · Plotly · Datos: Kaggle Netflix Shows dataset"
)
