# FixPack 13 — Seguimiento de Pruebas QA (v1.4)

Dashboard público en Streamlit con Excel versionado en GitHub.

## Fuente de datos

- **Archivo:** `data/Seguimiento_FixPack13.xlsx`
- **Hoja:** `PLAN GENERAL`
- **Cobertura actual:** primeros **1.774** registros con `Numero de caso` válido; los restantes se ignoran por ahora.
- El Excel **se publica con el repositorio**, por decisión expresa del equipo. Cualquier persona con acceso al repositorio puede descargar el archivo y sus versiones previas.
- No se deben agregar claves, contraseñas, tokens, datos identificables de clientes ni secretos.

## Ejecución local

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Primer despliegue con GitHub

1. Ve a https://github.com/new y crea `fixpack13-qa-dashboard` como repositorio **Public**. No crees otros archivos iniciales.
2. Abre esta carpeta descomprimida en VS Code.
3. Abre la terminal y ejecuta (cambia TU_USUARIO):

```powershell
git init
git add .
git status
git commit -m "Publicar FixPack 13 v1.4 con Excel de seguimiento"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/fixpack13-qa-dashboard.git
git push -u origin main
```

4. Entra a https://share.streamlit.io, vincula GitHub y selecciona **Create app**.
5. Elige `TU_USUARIO/fixpack13-qa-dashboard`, rama `main`, archivo `app.py`; escoge un subdominio disponible y pulsa **Deploy**.
6. Comprueba que el indicador de meta muestre **1.774** y que la aplicación se abra desde la nueva URL.

## Actualizar Excel sin volver a desplegar manualmente

- Modifica `data/Seguimiento_FixPack13.xlsx` en tu computador y guárdalo.
- En VS Code ejecuta:

```powershell
git add data/Seguimiento_FixPack13.xlsx
git commit -m "Actualizar avance de pruebas QA"
git push
```

- Alternativamente reemplaza el archivo desde GitHub → `data` → Add file → Upload files → Commit changes. **Debe conservar exactamente el mismo nombre**.
- Streamlit Community Cloud sincroniza los cambios confirmados en el repositorio. Si una sesión existente aún conserva la vista anterior, usa `↻ Actualizar vista` o recarga la página.

## Reglas actuales

- Meta: **1.774** escenarios, de los cuales **110** automatizados el primer día por Nicolás; las etiquetas inconsistentes de automatización del Excel no cambian la planificación.
- Manuales: 15 diarios por analista, excepto Adriana: 7. Nicolás comienza con manuales desde el segundo día.
- Paola ausente 03/12/2026 y 07/12/2026.
- Adriana de vacaciones 23/12/2026 a 17/01/2027; vuelve 18/01/2027.
- No laborables: sábados, domingos, 08/12/2026, 25/12/2026 y 01/01/2027.
- Inicio supuesto: 30/11/2026; editable en el panel lateral.
- Contingencia por defecto: 20% retest manual y 3 días de reserva.
- **Exitoso y Fallido** cuentan como ejecutados; **Bloqueado** no cuenta como ejecutado.
- Bugs asociados por columna `BUGS`; puede registrar varios ID separados por coma/punto y coma.

## Publicación

El proyecto solo se encuentra publicado cuando el repositorio remoto está creado y Streamlit Cloud confirma el deploy. El ZIP entregado es el código listo para cargar, no una URL pública activa.
