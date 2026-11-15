/* Exercise the actual inline browser implementation without a browser or network. */
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');
const { webcrypto } = require('node:crypto');

const html = readFileSync(join(__dirname, '../src/demo/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const core = script.split('// Initialize demo')[0];
const context = vm.createContext({ crypto: webcrypto, TextEncoder, TextDecoder, btoa, atob });
vm.runInContext(core, context);
const Shredder = vm.runInContext('VCPCryptoShredder', context);

test('empty browser chain is unresolved and does not create an event or key', async () => {
    const shredder = new Shredder();
    const result = await shredder.verifyChain();
    assert.equal(result.verified, false);
    assert.equal(result.status, 'INDETERMINATE');
    assert.equal(result.resultScope, 'LOCAL_PAYLOAD_HASH_CHAIN');
    assert.equal(result.eventsChecked, 0);
    assert.equal(result.errors.length, 0);
    assert.equal(shredder.eventChain.length, 0);
    assert.equal(shredder.keyStore.size, 0);
});

test('nonempty browser match remains a local result before and after key removal', async () => {
    const shredder = new Shredder();
    await shredder.createEvent('ORD', { symbol: 'SYNTHETIC' }, []);
    const before = JSON.stringify(shredder.eventChain);
    const result = await shredder.verifyChain();
    assert.equal(result.verified, true);
    assert.equal(result.status, 'VALID');
    assert.equal(result.resultScope, 'LOCAL_PAYLOAD_HASH_CHAIN');
    assert.equal(JSON.stringify(shredder.eventChain), before);
    await shredder.executeErasure();
    assert.equal((await shredder.verifyChain()).status, 'VALID');
});

test('browser payload mismatch is invalid without changing the supplied event', async () => {
    const shredder = new Shredder();
    await shredder.createEvent('ORD', { symbol: 'SYNTHETIC' }, []);
    shredder.eventChain[0].payload.symbol = 'changed';
    const before = JSON.stringify(shredder.eventChain);
    const result = await shredder.verifyChain();
    assert.equal(result.verified, false);
    assert.equal(result.status, 'INVALID');
    assert.equal(result.errors[0].error, 'EVENT_HASH_MISMATCH');
    assert.equal(JSON.stringify(shredder.eventChain), before);
});
