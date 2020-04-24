export class GPosition {
    /**
     * Creates an instance of cell.
     * @param sheet_name What sheet this cell corresponds to
     * @param row_idx The row index, starting from 0
     * @param col_idx The column index, starting from 0
     * @param text The text that is in the cell
     */
    constructor(sheet_name = "", row_idx = -1, col_idx = -1) {
        this._sheet = "";
        this._col = -1;
        this._row = -1;
        this._sheet = sheet_name;
        this._row = row_idx;
        this._col = col_idx;
    }
    /**
     * What sheet this cell corresponds to
     */
    get sheet() { return this._sheet; }
    /**
     * The column index, starting from 0
     */
    get col() { return this._col; }
    /**
     * The row index, starting from 0
     */
    get row() { return this._row; }
}
/**
 * Cell
 *
 * You can think of a Cell as a string with extra information about where it belongs in a
 * spreadsheet.  We have to keep that information around for the purposes of syntax highlighting,
 * debugging, etc.
 *
 * When a table is transformed (e.g. where it represents code that has itself undergone transformation),
 * the positional information represents that of the original table.  That way we can highlight that
 * cell during debugging.
 */
export class GCell extends GPosition {
    /**
     * Creates an instance of GCell.
     *
     * @param sheet_name What sheet this cell corresponds to
     * @param row_idx The row index, starting from 0
     * @param col_idx The column index, starting from 0
     * @param text The text that is in the cell
     */
    constructor(text, sheet_name = "", row_idx = -1, col_idx = -1) {
        super(sheet_name, row_idx, col_idx);
        this._text = text;
    }
    /**
     * The text that was entered into the cell
     */
    get text() { return this._text; }
    append(text) {
        this._text += text;
    }
    clone() {
        return new GCell(this._text, this._sheet, this._row, this._col);
    }
}
/**
 * GEntry
 *
 * An entry represents a key:value pair.
 *
 * When interpreted as a transducer, a Record is treated as a Literal.
 */
export class GEntry {
    constructor(key, value) {
        this._key = key;
        this._value = value;
    }
    get key() { return this._key; }
    get value() { return this._value; }
    clone() {
        return new GEntry(this._key.clone(), this._value.clone());
    }
    parse(input, symbol_table) {
        if (this.key.text == 'var') {
            // we're a VariableParser
            const parser = symbol_table.get(this._value.text);
            return parser.parse(input, symbol_table);
        }
        if (!input.has(this._key.text)) {
            // the input doesn't contain our tier, we're a generator
            var output = new GRecord();
            output.push(new GEntry(this.key, this.value));
            return [[output, input]];
        }
        // the input *does* contain our tier, so parse.
        var output = new GRecord();
        var remnant = new GRecord();
        // the result is going to be each entry in the input, with the target string
        // parsed off every tier of the appropriate name.  if any tier with a matching 
        // name doesn't begin with this, then the whole thing fails.
        for (const entry of input.entries) {
            if (entry.key.text != this.key.text) {
                // not the tier we're looking for, add it to the remnant and move on
                remnant.push(entry);
                continue;
            }
            if (!entry.value.text.startsWith(this.value.text)) {
                // parse failed! return the empty list
                return [];
            }
            const remnant_str = entry.value.text.slice(this.value.text.length);
            const remnant_cell = new GCell(remnant_str);
            const remnant_entry = new GEntry(this.key, remnant_cell);
            output.push(this);
            remnant.push(remnant_entry);
        }
        return [[output, remnant]];
    }
}
/**
 * Record
 *
 * A Record represnts a list of GEntries (key:value pairs); it's typically used as a dictionary
 * but keep in mind it's ordered and also allows repeat keys.
 *
 * When interpreted as a transducer, a Record is treated as a Concatenation of its entries,
 * in order.
 */
export class GRecord {
    constructor() {
        this._entries = [];
    }
    get entries() {
        return this._entries;
    }
    has(tier) {
        for (const entry of this._entries) {
            if (entry.key.text == tier) {
                return true;
            }
        }
        return false;
    }
    get(tier) {
        for (const entry of this._entries) {
            if (entry.key.text == tier) {
                return entry;
            }
        }
        throw new Error("Key not found: " + tier);
    }
    clone() {
        var result = new GRecord();
        for (const entry of this._entries) {
            result.push(entry.clone());
        }
        return result;
    }
    combine(other) {
        var result = this.clone();
        for (const other_entry of other.entries) {
            if (result.has(other_entry.key.text)) {
                var entry_to_change = result.get(other_entry.key.text);
                entry_to_change.value.append(other_entry.value.text);
                continue;
            }
            result.push(other_entry.clone());
        }
    }
    push(entry) {
        this._entries.push(entry);
    }
    parse(input, symbol_table) {
        return [];
    }
}
export class GTable {
    constructor() {
        this._records = [];
    }
    push(record) {
        this._records.push(record);
    }
    parse(input, symbol_table) {
        return [];
    }
}
export class SymbolTable {
    constructor() {
        this._symbols = new Map();
    }
    new_symbol(name) {
        this._symbols.set(name, new GTable());
    }
    has_symbol(name) {
        return this._symbols.has(name);
    }
    get(name) {
        const table = this._symbols.get(name);
        if (table == undefined) {
            throw new Error("Cannot find symbol " + name + " in symbol table");
        }
        return table;
    }
    add_to_symbol(name, record) {
        var table = this._symbols.get(name);
        if (table == undefined) {
            return;
        }
        table.push(record);
    }
}
