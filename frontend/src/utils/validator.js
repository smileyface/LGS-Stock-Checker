import Ajv from 'ajv';
import schemas from '../schema/server_schema.json';
import eventMap from '../schema/event_map.json';

// Initialize Ajv. strict: false is recommended for Pydantic schemas 
// as they often contain metadata fields (like 'title') that strict mode might reject.
const ajv = new Ajv({ strict: false });

const validators = new Map();

/**
 * Validates data against a specific schema model name.
 * @param {string} modelName - The key in server_schema.json (e.g., 'UserTrackedCardListSchema')
 * @param {any} data - The data to validate
 * @returns {boolean} - True if valid, False otherwise. Logs errors to console.
 */
export function validate(modelName, data) {
    if (!validators.has(modelName)) {
        const schema = schemas[modelName];
        if (!schema) {
            console.error(`Schema definition for '${modelName}' not found.`);
            return false;
        }
        validators.set(modelName, ajv.compile(schema));
    }

    const validateFn = validators.get(modelName);
    const valid = validateFn(data);

    if (!valid) {
        console.error(`Validation failed for '${modelName}':`, validateFn.errors);
    }

    return valid;
}

/**
 * Validates data based on the socket event name.
 * Automatically looks up the correct schema from event_map.json.
 * @param {string} eventName - The socket event name (e.g., 'cards_data')
 * @param {any} data - The data to validate
 * @returns {boolean}
 */
export function validateEvent(eventName, data) {
    const modelName = eventMap[eventName];
    if (!modelName) {
        console.warn(`No schema mapping found for event: '${eventName}'`);
        return false;
    }
    return validate(modelName, data);
}
