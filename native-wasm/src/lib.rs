//! Bounded static native analysis. Never executes a target binary.
use craft_anything_disasm::{Image, Limits, NoControl, Program, pseudo};
use serde_json::{json, Value};
use std::sync::Arc;
use wasm_bindgen::prelude::*;

const MAX_INPUT:usize=64*1024*1024;
const MAX_OUTPUT:usize=24*1024*1024;

fn limits()->Limits {
    Limits { max_functions: 2000, max_insns_per_function: 6000,
        max_total_insns: 400_000, max_xrefs: 150_000, max_strings: 5000,
        string_min_len: 4, max_data_scan: 8*1024*1024, scan_prologues:true }
}
fn analyze_image(img:&Image, offset:usize, count:usize)->Result<Value,String>{
    let prog=Program::analyze(img,&limits(),&NoControl).map_err(|e|e.to_string())?;
    let n=prog.functions.len();
    let page_size=count.clamp(1,128);
    let mut functions=Vec::new();
    let mut output_bytes=0usize;
    let mut skipped_due_to_output=false;
    for f in prog.functions.values().skip(offset).take(page_size) {
        let p=pseudo::lift(img,&prog,f,&|_|None);
        let row=json!({"entry":format!("0x{:x}",f.entry),"name":f.name,
            "instruction_count":f.insn_count,"discovered_by":f.discovered_by,
            "truncated":f.truncated,"blocks":f.blocks,"calls":f.calls,
            "pseudo_c":p.text,"signature":p.signature,"structured":p.structured,
            "asm_fallbacks":p.asm_fallbacks,"limitations":p.limitations});
        let size=serde_json::to_vec(&row).map_err(|e|e.to_string())?.len();
        if output_bytes.saturating_add(size)>MAX_OUTPUT {skipped_due_to_output=true;break;}
        output_bytes+=size; functions.push(row);
    }
    let next=offset.saturating_add(functions.len());
    Ok(json!({"format":format!("{:?}",img.bin.format),"architecture":format!("{:?}",img.bin.arch),
        "stats":prog.stats,"limitations":prog.limitations,"total_functions":n,"offset":offset,
        "next_offset":if next<n&&next>offset{Some(next)}else{None},
        "output_limit_reached":skipped_due_to_output,"functions":functions,
        "provenance":"Inferred register-level pseudo-C, not original or necessarily compilable source."}))
}

#[wasm_bindgen]
pub fn decompile_native(bytes:&[u8],offset:u32,count:u32)->Result<String,JsValue>{
    if bytes.is_empty()||bytes.len()>MAX_INPUT{return Err(JsValue::from_str("Input must be 1 byte–64 MiB"));}
    let img=Image::parse(Arc::<[u8]>::from(bytes)).map_err(|e|JsValue::from_str(&e.to_string()))?;
    let report=analyze_image(&img,offset as usize,count as usize).map_err(|e|JsValue::from_str(&e))?;
    serde_json::to_string(&report).map_err(|e|JsValue::from_str(&e.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use craft_anything_formats::Arch;
    #[test]
    fn lifts_known_x86_code() {
        // mov eax, 42; ret -- genuine machine-code fixture.
        let img=Image::raw(Arc::<[u8]>::from([0xb8u8,42,0,0,0,0xc3].as_slice()),Arch::X86,0x1000);
        let report=analyze_image(&img,0,32).expect("native fixture analysis");
        assert!(report["total_functions"].as_u64().unwrap_or(0)>0);
        let first=&report["functions"][0];
        assert!(first["pseudo_c"].as_str().unwrap_or("").contains("42")||
                first["pseudo_c"].as_str().unwrap_or("").contains("0x2a"));
    }
}
