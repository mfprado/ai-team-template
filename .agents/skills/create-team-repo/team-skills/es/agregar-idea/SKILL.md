---
name: agregar-idea
description: Sumar una idea para el espacio de IA del equipo a las ideas del equipo y, cuando la idea es sobre una forma de trabajar, dibujar su flujo como un diagrama que el equipo ve en la página del equipo. Usala cuando alguien dice "tengo una idea", "estaría bueno que", "podríamos automatizar", "agregá una idea", o describe un proceso en el que le gustaría que la IA ayude.
allowed-tools: Bash(sh .agents/system/bin/py -I .agents/system/scripts/ideas.py *) Bash(sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py *)
---

# Agregar una idea

## Flujo

```mermaid
flowchart TD
    A([Alguien comparte una idea]):::done --> B{{¿Tiene un título corto?}}
    B -- No --> C[Pedir un título en pocas palabras] --> D
    B -- Sí --> D{{¿Es sobre una forma de trabajar?}}
    D -- No --> F[Guardar la idea]
    D -- Sí --> E[Dibujar el flujo y mostrarlo] --> G{{¿Está bien?}}
    G -- No --> H[Corregir el diagrama] --> G
    G -- Sí --> F
    F --> I([Guardarla para el equipo]):::done
    %% A: La persona cuenta, con sus palabras, algo que ayudaría al equipo.
    %% B: El título es de la persona: unas pocas palabras que nombran la idea.
    %% C: Una sola pregunta corta. Nunca inventarle el título.
    %% D: Una forma de trabajar: pasos que sigue la gente, quién hace qué, con qué herramientas, qué sale al final (un reporte cada lunes, responder mails de clientes, sumar a alguien nuevo).
    %% E: Dibuja todo el flujo de una vez con lo que contó la persona y lo muestra en el chat.
    %% F: Suma la idea a las ideas del equipo, con su descripción y el diagrama si lo tiene.
    %% I: La comparte con el equipo enseguida; aparece en la página del equipo, en Ideas.
```

## Pasos

1. **Título.** Usá las palabras de la persona. Si no dio un título corto, pedile uno en pocas
   palabras (una sola pregunta). Nunca lo inventes.

2. **¿Es una forma de trabajar?** Si la idea describe pasos que sigue la gente (quién empieza,
   qué pasa después, con qué herramientas, qué sale al final), dibujá su flujo. Si es otra cosa
   (una herramienta para probar, una capacitación, una página), pasá al paso 4.

3. **Dibujá el flujo de una vez**, con lo que te contó la persona, y mostralo en el chat como un
   bloque `mermaid`. Usá el mismo estilo que las skills del equipo:
   - `flowchart TD`, pasos en palabras simples y cortas, en español.
   - El primer y el último paso redondeados y marcados: `A([...]):::done`.
   - Las preguntas como `{{...?}}` con `-- Sí -->` / `-- No -->`.
   - Una línea `%% <letra>: <una frase simple>` por paso, que diga qué pasa ahí.
   - Como mucho unos 12 pasos. Lo que no sepas, dejalo como pregunta en las notas en vez de inventarlo.

   Preguntá en una línea si está bien. Corregilo hasta que diga que sí.

4. **Guardá la idea**, con la descripción en las palabras de la persona:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/ideas.py add --title "<título>" --text "<descripción>"
   ```

   Responde con el `id` de la idea. Si hay diagrama, escribilo en un archivo temporal (fuera de
   la carpeta del equipo) y sumalo:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/ideas.py flow --id <id> --file "<archivo temporal>"
   ```

5. **Guardala para el equipo** enseguida:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py --summary "Nueva idea: <título>" --paths IDEAS.md .agents/ideas
   ```

   Contale en una línea que la idea está en la página del equipo, en Ideas, con su flujo si lo
   tiene ("Ver el flujo").
