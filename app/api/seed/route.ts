import {seedCorpus,corpusStatus} from '../../../lib/corpus';
import {failure,json,sameOrigin} from '../../../lib/server';
export const dynamic='force-dynamic';
// Shared immutable corpus only. Sites enforces the owner-private deployment boundary.
// User scenarios and runs always require their own authenticated visitor identity.
export async function POST(request:Request){if(!sameOrigin(request))return json({error:'Origem inválida'},403);try{return json(await seedCorpus());}catch(e){return failure(e);}}
export async function GET(){try{return json(await corpusStatus());}catch(e){return failure(e);}}
