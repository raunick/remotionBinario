#!/usr/bin/env node

const sharp = require('sharp');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

const argv = yargs(hideBin(process.argv))
    .usage('Usage: $0 [files] [options]')
    .option('height', {
        alias: 'h',
        type: 'number',
        description: 'Target height (preserves aspect ratio)',
    })
    .option('width', {
        alias: 'w',
        type: 'number',
        description: 'Target width (preserves aspect ratio)',
    })
    .option('dither', {
        type: 'boolean',
        description: 'Enable Floyd-Steinberg dithering',
        default: false,
    })
    .option('invert', {
        type: 'boolean',
        description: 'Invert colors (for OLEDs where on=white)',
        default: false,
    })
    .option('c-header', {
        alias: 'c',
        type: 'boolean',
        description: 'Generate C header file output',
        default: true,
    })
    .option('threshold', {
        type: 'number',
        description: 'Threshold for b/w conversion (0-255)',
        default: 128,
    })
    .option('spritesheet', {
        alias: 's',
        type: 'boolean',
        description: 'Combine inputs into a horizontal sprite sheet',
        default: false,
    })
    .demandCommand(1)
    .help()
    .argv;

async function processImage(file, index, total) {
    const filename = path.basename(file, path.extname(file));
    console.log(chalk.blue(`Processing [${index + 1}/${total}]: ${filename}`));

    try {
        let pipeline = sharp(file);

        // 1. Trim (Auto-crop)
        pipeline = pipeline.trim();

        // 2. Resize
        const resizeOpts = {
            fit: 'contain',
            background: { r: 0, g: 0, b: 0, alpha: 0 },
            kernel: sharp.kernel.nearest // Pixel-perfect scaling
        };
        if (argv.height) resizeOpts.height = argv.height;
        if (argv.width) resizeOpts.width = argv.width;

        if (argv.height || argv.width) {
            pipeline = pipeline.resize(resizeOpts);
        }

        // 3. Flatten & Grayscale
        // Flatten alpha: white background default, or black if inverted requested?
        // Actually standard is white background for drawings.
        pipeline = pipeline
            .flatten({ background: { r: 255, g: 255, b: 255 } })
            .grayscale();

        // 4. Invert (Negative)
        if (argv.invert) {
            pipeline = pipeline.negate();
        }

        // 5. Apply Dithering / Thresholding
        // We need to bake this into a buffer to get the final pixel values
        // Sharp only dithers on output to palette formats (PNG/GIF)
        let processedBuffer, info;

        if (argv.dither) {
            // Output as 2-color PNG to force Floyd-Steinberg dithering
            const pngBuffer = await pipeline.png({
                palette: true,
                colors: 2,
                dither: 1.0
            }).toBuffer();

            // Reload the dithered PNG as raw pixels (00 or FF)
            const reloaded = sharp(pngBuffer).ensureAlpha(); // Ensure we have consistent channels (though we want 'raw' 1 channel)
            const res = await reloaded.raw().toBuffer({ resolveWithObject: true });
            processedBuffer = res.data;
            info = res.info;

            // The reloaded raw might be 3 or 4 channels (RGB/RGBA) depending on PNG palette expansion
            // We need to extract just one channel (Luminance)
            if (info.channels > 1) {
                processedBuffer = await sharp(pngBuffer).grayscale().raw().toBuffer();
            } else {
                processedBuffer = res.data;
            }

        } else {
            // Simple Threshold
            const res = await pipeline.threshold(argv.threshold).raw().toBuffer({ resolveWithObject: true });
            processedBuffer = res.data;
            info = res.info;
        }

        return {
            name: filename,
            path: file,
            buffer: processedBuffer,
            width: info.width || argv.width, // fallback
            height: info.height || argv.height
        };

    } catch (error) {
        console.error(chalk.red(`Error processing ${file}:`), error.message);
        return null;
    }
}

function generateCHeader(name, buffer, width, height) {
    // Convert 8-bit grayscale buffer to 1-bit packed (Row-major, MSB first - Adafruit GFX standard)
    const byteWidth = Math.ceil(width / 8);
    const totalBytes = byteWidth * height;
    const bitmap = new Uint8Array(totalBytes);

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const pixelVal = buffer[y * width + x];
            // Assuming 0 is black (off), >128 is white (on)
            if (pixelVal > 128) {
                bitmap[y * byteWidth + Math.floor(x / 8)] |= (0x80 >> (x % 8));
            }
        }
    }

    const cleanName = name.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();

    let hexData = '';
    for (let i = 0; i < bitmap.length; i++) {
        hexData += `0x${bitmap[i].toString(16).padStart(2, '0').toUpperCase()}`;
        if (i < bitmap.length - 1) hexData += ', ';
        if ((i + 1) % 12 === 0) hexData += '\n  ';
    }

    return `// Generated by svg2sprite - do not edit
// Source: ${name}
// Size: ${width}x${height}

#ifndef _BMP_${cleanName.toUpperCase()}_H_
#define _BMP_${cleanName.toUpperCase()}_H_

#include <stdint.h>
#include <pgmspace.h>

const unsigned char bitmap_${cleanName}[] PROGMEM = {
  ${hexData}
};

#endif // _BMP_${cleanName.toUpperCase()}_H_
`;
}

async function saveOutput(name, buffer, width, height, dir) {
    const outBase = path.join(dir, name);

    // Save PNG Preview (pixel perfect)
    await sharp(buffer, { raw: { width, height, channels: 1 } })
        .png({ colors: 2 })
        .toFile(`${outBase}_preview.png`);
    console.log(chalk.gray(`  -> Saved preview: ${outBase}_preview.png`));

    // Save C Header
    if (argv['c-header']) {
        const header = generateCHeader(name, buffer, width, height);
        await fs.writeFile(`${outBase}.h`, header);
        console.log(chalk.green(`  -> Saved C Header: ${outBase}.h`));
    }
}

// Main execution
(async () => {
    const files = argv._;
    if (files.length === 0) {
        console.error(chalk.red('No input files provided.'));
        process.exit(1);
    }

    const results = [];
    for (let i = 0; i < files.length; i++) {
        const res = await processImage(files[i], i, files.length);
        if (res) results.push(res);
    }

    if (results.length === 0) return;

    const outputDir = path.dirname(results[0].path);

    // Mode 1: Sprite Sheet (Combine all)
    if (argv.spritesheet && results.length > 0) {
        console.log(chalk.yellow('\nGenerating Sprite Sheet...'));

        const totalWidth = results.reduce((sum, r) => sum + r.width, 0);
        const maxHeight = Math.max(...results.map(r => r.height));

        // Create composite buffer
        // 8-bit grayscale 
        const sheetBuffer = new Uint8Array(totalWidth * maxHeight).fill(0); // Fill black (or white?) 0 is black.

        let currentX = 0;
        for (const res of results) {
            // Copy rows
            for (let y = 0; y < res.height; y++) {
                for (let x = 0; x < res.width; x++) {
                    const val = res.buffer[y * res.width + x];
                    sheetBuffer[y * totalWidth + (currentX + x)] = val;
                }
            }
            // Log frame info
            console.log(`  Frame ${res.name}: x=${currentX}, w=${res.width}`);
            currentX += res.width;
        }

        const sheetName = "spritesheet"; // Could be customized
        await saveOutput(sheetName, sheetBuffer, totalWidth, maxHeight, outputDir);

        console.log(chalk.magenta(`\nSprite Sheet Created: ${totalWidth}x${maxHeight}`));

    } else {
        // Mode 2: Individual Files
        for (const res of results) {
            await saveOutput(res.name, res.buffer, res.width, res.height, outputDir);
        }
    }

})();
