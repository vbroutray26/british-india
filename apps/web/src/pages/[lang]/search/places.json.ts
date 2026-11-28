// Place index for autocomplete, one per language (labels translated; names as printed).
import type { APIRoute } from 'astro';
import { LOCALES, type Locale } from '../../../i18n';
import { typeLabel } from '../../../i18n/labels';
import { ancestors, nameOf, places, searchNames, slugOf } from '../../../data/curated';
import type { PlaceIndexItem } from '../../../search/places';

export function getStaticPaths() {
  return LOCALES.map((lang) => ({ params: { lang } }));
}

export const GET: APIRoute = ({ params }) => {
  const lang = params.lang as Locale;
  const items: PlaceIndexItem[] = places.map((p) => {
    const district = ancestors(p).find((a) => a.type === 'district');
    return { id: p.place_id, name: nameOf(p, lang), aliases: searchNames(p).filter((n) => n !== nameOf(p, lang)), type: typeLabel(p.type, lang),
      district: district ? nameOf(district, lang) : undefined, href: `/${lang}/places/${slugOf(p.place_id)}/` };
  });
  return new Response(JSON.stringify(items), { headers: { 'Content-Type': 'application/json' } });
};
