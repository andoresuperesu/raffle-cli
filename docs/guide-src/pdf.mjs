import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const [,, html, pdf] = process.argv;
const b = await chromium.launch();
const p = await b.newPage();
await p.goto('file://' + html);
await p.pdf({ path: pdf, format: 'A4', printBackground: true, displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#6b7280;font-family:Helvetica">how raffle-cli was built &nbsp;·&nbsp; <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  margin: { top: '18mm', bottom: '20mm', left: '16mm', right: '16mm' } });
await b.close();
