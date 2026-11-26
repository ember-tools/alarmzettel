/**
 * What the script linters read, relative to the repository root: the frontend and its configs, the
 * backend, its tools, and for the em dash also the styles, the page shell, the interrogation tree
 * served to the browser, the Typst templates, the image, compose and CI files, the toolchain, the
 * Nix shell and the READMEs.
 */
export default {
    root: '..',
    sources: [
        {path: 'frontend/src', extensions: ['.ts', '.vue']},
        {path: 'frontend/vite.config.ts', extensions: null},
        {path: 'frontend/eslint.config.mjs', extensions: null},
        {path: 'frontend/emberbox-lint.config.mjs', extensions: null},
        {path: 'backend/src', extensions: ['.py']},
        {path: 'tools', extensions: ['.py', '.mjs']},
    ],
    text: [
        {path: 'frontend/src', extensions: ['.css']},
        {path: 'frontend/index.html', extensions: null},
        {path: 'frontend/public/sna-tree.json', extensions: null},
        {path: 'backend/src/render', extensions: ['.typ']},
        {path: 'Dockerfile', extensions: null},
        {path: 'compose.yml', extensions: null},
        {path: 'compose.prod.yml', extensions: null},
        {path: 'compose.dev.yml', extensions: null},
        {path: '.github', extensions: ['.yml']},
        {path: 'toolchain.sh', extensions: null},
        {path: 'shell.nix', extensions: null},
        {path: '.dockerignore', extensions: null},
        {path: '.gitignore', extensions: null},
        {path: 'backend/.gitignore', extensions: null},
        {path: 'backend/src/render/fonts/README.md', extensions: null},
        {path: 'README.md', extensions: null},
    ],
    browserStorage: {catalogue: 'frontend/browser-storage.json', sources: 'frontend/src'},
    duplication: '.jscpd.json',
}
