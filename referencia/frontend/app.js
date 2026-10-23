// Frontend sin frameworks: Cognito y la API se llaman con fetch.
// config.json lo genera CDK al desplegar (región, URL de la API y cliente de Cognito).

let config;
const $ = (selector) => document.querySelector(selector);

function mostrar(texto, esError = false) {
  $("#mensaje").textContent = texto;
  $("#mensaje").className = esError ? "error" : "";
}

// --- Cognito: API JSON pública, no requiere SDK ---

async function cognito(accion, cuerpo) {
  const r = await fetch(`https://cognito-idp.${config.region}.amazonaws.com/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": `AWSCognitoIdentityProviderService.${accion}`,
    },
    body: JSON.stringify({ ClientId: config.clienteId, ...cuerpo }),
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(datos.message || datos.__type);
  return datos;
}

async function entrar(email, clave) {
  const datos = await cognito("InitiateAuth", {
    AuthFlow: "USER_PASSWORD_AUTH",
    AuthParameters: { USERNAME: email, PASSWORD: clave },
  });
  // El access token dura 1 hora. sessionStorage se borra al cerrar la pestaña.
  sessionStorage.setItem("token", datos.AuthenticationResult.AccessToken);
}

// --- API de tareas ---

async function api(metodo, ruta, cuerpo) {
  const r = await fetch(config.apiUrl.replace(/\/$/, "") + ruta, {
    method: metodo,
    headers: {
      Authorization: `Bearer ${sessionStorage.getItem("token")}`,
      "Content-Type": "application/json",
    },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  if (r.status === 401) {
    salir();
    throw new Error("La sesión expiró. Vuelva a entrar.");
  }
  const datos = r.status === 204 ? null : await r.json();
  if (!r.ok) throw new Error(datos?.error || `Error ${r.status}`);
  return datos;
}

async function cargarTareas() {
  const tareas = await api("GET", "/tareas");
  const lista = $("#lista");
  lista.replaceChildren(...tareas.map(elementoTarea));
  if (tareas.length === 0) mostrar("Aún no tiene tareas.");
}

function elementoTarea(tarea) {
  const li = document.createElement("li");
  li.classList.toggle("completada", tarea.completada);

  const check = document.createElement("input");
  check.type = "checkbox";
  check.checked = tarea.completada;
  check.setAttribute("aria-label", "Completada");
  check.onchange = () => accion(() => api("PUT", `/tareas/${tarea.tareaId}`, { completada: check.checked }));

  // textContent (no innerHTML) para que un título no pueda inyectar HTML.
  const titulo = document.createElement("span");
  titulo.textContent = tarea.titulo;
  titulo.title = "Doble clic para editar";
  titulo.ondblclick = () => {
    const nuevo = prompt("Editar tarea", tarea.titulo);
    if (nuevo && nuevo.trim() !== tarea.titulo) {
      accion(() => api("PUT", `/tareas/${tarea.tareaId}`, { titulo: nuevo }));
    }
  };

  const borrar = document.createElement("button");
  borrar.textContent = "Borrar";
  borrar.className = "secundario";
  borrar.onclick = () => accion(() => api("DELETE", `/tareas/${tarea.tareaId}`));

  li.append(check, titulo, borrar);
  return li;
}

// Ejecuta un cambio, recarga la lista y muestra el error si algo falla.
async function accion(fn) {
  mostrar("");
  try {
    await fn();
    await cargarTareas();
  } catch (e) {
    mostrar(e.message, true);
  }
}

// --- Pantallas ---

function pantalla() {
  const conSesion = Boolean(sessionStorage.getItem("token"));
  $("#acceso").hidden = conSesion;
  $("#tareas").hidden = !conSesion;
  if (conSesion) accion(() => Promise.resolve());
}

function salir() {
  sessionStorage.removeItem("token");
  pantalla();
}

function enviar(selector, fn) {
  $(selector).onsubmit = async (e) => {
    e.preventDefault();
    const datos = Object.fromEntries(new FormData(e.target));
    mostrar("");
    try {
      await fn(datos, e.target);
    } catch (error) {
      mostrar(error.message, true);
    }
  };
}

let emailPendiente;

enviar("#form-entrar", async ({ email, clave }) => {
  await entrar(email, clave);
  pantalla();
});

enviar("#form-registro", async ({ email, clave }) => {
  await cognito("SignUp", {
    Username: email,
    Password: clave,
    UserAttributes: [{ Name: "email", Value: email }],
  });
  emailPendiente = { email, clave };
  $("#email-confirmar").textContent = email;
  $("#form-confirmar").hidden = false;
  mostrar("Cuenta creada. Revise su correo.");
});

enviar("#form-confirmar", async ({ codigo }, form) => {
  await cognito("ConfirmSignUp", { Username: emailPendiente.email, ConfirmationCode: codigo });
  await entrar(emailPendiente.email, emailPendiente.clave);
  form.hidden = true;
  pantalla();
});

enviar("#form-nueva", async ({ titulo }, form) => {
  await accion(() => api("POST", "/tareas", { titulo }));
  form.reset();
});

$("#salir").onclick = salir;

fetch("config.json")
  .then((r) => r.json())
  .then((c) => {
    config = c;
    pantalla();
  })
  .catch(() => mostrar("No se encontró config.json. ¿Ya se desplegó con CDK?", true));
