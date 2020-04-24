
export class GPosition {

    protected _sheet: string = "";
    protected _col: number = -1;
    protected _row: number = -1;
    
    /**
     * What sheet this cell corresponds to 
     */
    public get sheet(): string { return this._sheet; }
    /**
     * The column index, starting from 0
     */
    public get col(): number { return this._col; }
    /**
     * The row index, starting from 0
     */
    public get row(): number { return this._row; }

    /**
     * Creates an instance of cell.
     * @param sheet_name What sheet this cell corresponds to 
     * @param row_idx The row index, starting from 0 
     * @param col_idx The column index, starting from 0
     * @param text The text that is in the cell
     */
    constructor(sheet_name: string = "", row_idx: number = -1, col_idx: number = -1) {
        this._sheet = sheet_name;
        this._row = row_idx;
        this._col = col_idx;
    }
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

    protected _text: string; 
    
    /**
     * The text that was entered into the cell
     */
    public get text(): string { return this._text; }

    /**
     * Creates an instance of GCell.
     * 
     * @param sheet_name What sheet this cell corresponds to 
     * @param row_idx The row index, starting from 0 
     * @param col_idx The column index, starting from 0
     * @param text The text that is in the cell
     */
    constructor(text: string, sheet_name: string = "", row_idx: number = -1, col_idx: number = -1) {
        super(sheet_name, row_idx, col_idx);
        this._text = text;
    }

    public append(text: string): void {
        this._text += text;
    }

    public clone(): GCell {
        return new GCell(this._text, this._sheet, this._row, this._col);
    }
}


interface ITransducer {

    parse(input: GRecord, symbol_table: SymbolTable): [GRecord, GRecord][];

}

/**
 * GEntry
 * 
 * An entry represents a key:value pair.
 * 
 * When interpreted as a transducer, a Record is treated as a Literal.
 */
export class GEntry implements ITransducer {

    private _key: GCell;
    private _value: GCell;

    public constructor(key: GCell, value: GCell) {
        this._key = key;
        this._value = value;
    }

    public get key(): GCell { return this._key; }
    public get value(): GCell { return this._value; }
    
    public clone(): GEntry {
        return new GEntry(this._key.clone(), this._value.clone());
    }

    public parse(input: GRecord, symbol_table: SymbolTable): [GRecord, GRecord][] {

        if (this.key.text == 'var') {
            // we're a VariableParser
            const parser = symbol_table.get(this._value.text);
            return parser.parse(input, symbol_table);
        }

        if (!input.has(this._key.text)) {
            // the input doesn't contain our tier, we're a generator
            var output = new GRecord();
            output.push(new GEntry(this.key, this.value));
            return [ [output, input ]];
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

        return [ [output, remnant] ];
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

export class GRecord implements ITransducer {

    private _entries : GEntry[] = [];

    public get entries(): GEntry[] {
        return this._entries;
    }

    public has(tier: string): boolean {
        for (const entry of this._entries) {
            if (entry.key.text == tier) {
                return true;
            }
        }
        return false;
    }

    public get(tier: string): GEntry {
        for (const entry of this._entries) {
            if (entry.key.text == tier) {
                return entry;
            }
        }
        throw new Error("Key not found: " + tier);
    }

    public clone(): GRecord {
        var result = new GRecord();
        for (const entry of this._entries) {
            result.push(entry.clone());
        }
        return result;
    }

    public combine(other: GRecord) {
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

    public push(entry: GEntry): void {
        this._entries.push(entry);
    }

    public parse(input: GRecord, symbol_table: SymbolTable): [GRecord, GRecord][] {
        return [];
    }

}


export class GTable implements ITransducer {

    private _records : GRecord[] = [];

    public push(record: GRecord) {
        this._records.push(record);
    }

    public parse(input: GRecord, symbol_table: SymbolTable): [GRecord, GRecord][] {
        return [];
    }
}

export class SymbolTable {

    private _symbols : Map<string, GTable> = new Map();

    public new_symbol(name: string) {
        this._symbols.set(name, new GTable());
    }

    public has_symbol(name: string): boolean {
        return this._symbols.has(name);
    }

    public get(name: string): GTable {
        const table = this._symbols.get(name);
        if (table == undefined) {
            throw new Error("Cannot find symbol " + name + " in symbol table");
        } 
        return table;
    }

    public add_to_symbol(name: string, record: GRecord) {
        var table = this._symbols.get(name);
        if (table == undefined) {
            return;
        }
        table.push(record);
    }
}
