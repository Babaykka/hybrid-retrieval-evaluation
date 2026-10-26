import path from 'node:path';
import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const ROOT=(process.env.PROJECT_ROOT||process.cwd());
const BUILD=ROOT+'/presentation_2026/review_2026-10-12/build';
const SKILL=(process.env.PRESENTATIONS_SKILL||'');
process.env.RUNTIME_NODE_MODULES=(process.env.RUNTIME_NODE_MODULES||'');
const {finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
await fs.mkdir(BUILD+'/validated',{recursive:true});
const result=await finalizePresentation({
 workspaceDir:ROOT,candidatePath:BUILD+'/candidate.pptx',
 finalPath:BUILD+'/validated/validated_v3.pptx',
 pythonExecutable:(process.env.PYTHON||'python3'),
 integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
 explicitTotalSlideCount:26,
 requiredNativeTableOwnerSlides:[2,3,4,17,21,22,23,24,25],
 requiredNativeChartOwnerSlides:[8,10,13,15,16],
 requiredEmbeddedWorkbookChartOwnerSlides:[8,10,13,15,16],
 materializeLiteralChartWorkbooks:false,
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,3,4,17,21,22,23,24,25].flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'reference',families:['Arial'],referencePath:BUILD+'/source/presentation.pptx',referenceSha256:'f75bc5677f974d9ebdea6690db8c3e22ed602df05795c410498d43f17804df75'},
 verifyArtifactToolImport:true,receiptPath:BUILD+'/final_v3.validation.json'
});
console.log(JSON.stringify(result,null,2));
