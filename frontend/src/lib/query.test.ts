import { describe, expect, it } from 'vitest';
import { toSearchParams } from './query';

describe('toSearchParams', () => {
  it('omits empty, null and undefined values and trims text', () => {
    const params = toSearchParams({
      store_id: '  ST001 ',
      sku: '',
      product_name: undefined,
      min_price: null,
      page: 2,
    });

    expect(params.toString()).toBe('store_id=ST001&page=2');
  });

  it('encodes special characters', () => {
    expect(toSearchParams({ product_name: '100% juice & more' }).toString()).toBe(
      'product_name=100%25+juice+%26+more',
    );
  });
});
