import { preview } from 'vite';
import { fileURLToPath } from 'node:url';
// Serve the tested production build; no development compiler is needed at startup.
const server = await preview({configFile:false, root:fileURLToPath(new URL('.', import.meta.url)), preview:{host:'127.0.0.1',port:5174,strictPort:true}});
server.printUrls();
