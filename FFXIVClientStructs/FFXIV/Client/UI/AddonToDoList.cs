using System.Runtime.Intrinsics.X86;
using FFXIVClientStructs.FFXIV.Component.GUI;

namespace FFXIVClientStructs.FFXIV.Client.UI;

// Client::UI::AddonNamePlate
//   Component::GUI::AtkUnitBase
//     Component::GUI::AtkEventListener
[Addon("_ToDoList")]
[GenerateInterop]
[Inherits<AtkUnitBase>]
[StructLayout(LayoutKind.Explicit, Size = 0x4C0)]
[VirtualTable("48 8D 05 ?? ?? ?? ?? 48 8D 8B ?? ?? ?? ?? 48 89 03 E8 ?? ?? ?? ?? 33 C0 C7 83 ?? ?? ?? ?? ?? ?? ?? ?? 48 8D 8B ?? ?? ?? ?? 48 89 83 ?? ?? ?? ?? 33 D2 48 89 83 ?? ?? ?? ?? 41 B8 ?? ?? ?? ?? 48 89 83 ?? ?? ?? ?? 48 89 83 ?? ?? ?? ?? 48 89 83 ?? ?? ?? ??", 3)]
public unsafe partial struct AddonToDoList {

    /*
     * sastasha also 2002696
     * 0x238 - vtable
     * 0x240 - NodeHolder*
     * 0x248 - NodeHolder* (but it's AtkEventTarget* inside)
     * 0x250 - ptr?
     * 0x258 - 0x9001 // not sure what this is but it seems pretty stable
     * 0x25A - ??? 0x67 turn2, 8f turn1, 0x0255 mji, 0xb7 sastasha
     * 0x260 - ptr -> duty timer text node
     * 0x268
     * 0x270
     * 0x278
     * 0x280
     * 0x288
     * 0x290 - ptr - only seems populated _in_ duty
     *  - 4 blank int64
     *  - ptr to "Duty Information" collision node 
     *  - 5 blank int64
     *  - 2x ptr to AtkEventTarget (this may be outside the object)
     * 0x298 - ptr (feels similar to the second NodeHolder above, but with no AtkEventTargets until ptr6?)- was immediately after duty information node 
     * 0x2a0 - ptr? probably some third list like above but no idea what
     * 0x2b8~0x30C
     *  - [] button action, idx, idx << 5 ?
     * rest zero?
    */


    [GenerateInterop]
    [StructLayout(LayoutKind.Explicit, Size = 0x10)]
    public partial struct NodeHolder {
        [FieldOffset(0x0)] private AtkComponentNode* node; // but some of these can be AtkEventTargets??
        [FieldOffset(0x8)] private int unk8; // seems to always be 2
        [FieldOffset(0xC)] private short unkC; // Seems to be either 3, -2, 0 (for duty info hdr+detail)
        [FieldOffset(0xE)] private short unkE; // Seems to be either 0x1E, 0x16, or 0x32, 0x24
    }
    
    
    [GenerateInterop]
    [StructLayout(LayoutKind.Explicit, Size = 197 * 4)]
    public partial struct AddonToDoListNumberArray {
        public static AddonToDoListNumberArray* Instance() => (AddonToDoListNumberArray*)AtkStage.Instance()->GetNumberArrayData(NumberArrayType.ToDoList)->IntArray;

        // 0 - unk
        // 1 - unk
        // 2 - 1 in duty, 0 otherwise?
        [FieldOffset(0x8)] public int DutyTimerEnabled;
        // 3 - unk
        // 4 - 1 when queueing, 2 in duty
        // 5 - 1 when queueing
        // 6 - queueState? 4 -> waiting, 3-> filled, 1-> 
        
        [FieldOffset(0x1C)] public bool QuestListEnabled;
        [FieldOffset(0x20)] public int QuestCount;
        [FieldOffset(0x24)] [FixedSizeArray] internal FixedSizeArray10<int> _questTypeIcon;

        [FieldOffset(0x4C)] [FixedSizeArray] internal FixedSizeArray10<int> _enable; // Seems to be a generic enable flag for the quest
        [FieldOffset(0x9C)] [FixedSizeArray] internal FixedSizeArray10<int> _buttonCountForEntry;

        // values are either an itemID or an emoteID|0x2000000
        [FieldOffset(0xC4)] [FixedSizeArray] internal FixedSizeArray40<int> _actionID;

        // 59-88 ??

        [FieldOffset(0x164)] [FixedSizeArray] internal FixedSizeArray40<int> _iconID;
        
        // 129 - dutyTimerEnabled
        // 130 - duty icon id

        [FieldOffset(0x220)] public int DutyObjectiveCount;
        [FieldOffset(0x224)] [FixedSizeArray] internal FixedSizeArray10<int> _dutyObjectiveStates;
        
        // -1 is N/A, otherwise in range 0~100 for percentage
        [FieldOffset(0x24C)] [FixedSizeArray] internal FixedSizeArray10<int> _dutyObjectivePercentage;

        
        // 136 - number of duty objectives to display
        // 137~146 duty objective... state? 4 seems to be checkmark? unclear how many - guessing 10 based on offsets
        // 147-156 objective progress in pct, -1 for hidden objectives
        // 167 - seems to be tracking overall duty state somehow
        // 1 after first miniboss
        // -196 ??
    }


    [GenerateInterop]
    [StructLayout(LayoutKind.Explicit, Size = 211 * 8)]
    public partial struct AddonToDoListStringArray {
        public static AddonToDoListStringArray* Instance() => (AddonToDoListStringArray*)AtkStage.Instance()->GetStringArrayData(StringArrayType.ToDoList)->StringArray;
        [FieldOffset(0)] [FixedSizeArray] internal FixedSizeArray211<nint> _strings;
        
        /* String array
         * 0 - Duty finder queue title
         * 1-4 - unk
         * 5 - blank?
         * 6 - duty finder status message
         * 7 - duty finder wait info
         * 8 - unk
         * 19-28 - packed titles then packed details, no gaps
         *
         * 159 - active duty title
         * 160 - blank?
         * 161 - unk
         * 162 - duty timer
         * 163-164 - blank?
         * 165-174 - duty objective text
         * 119-158 - button labels
         * 210 - "Duty Finder" / "Duty Information"
         * 211 - "Readying duty..." / ""
         */
    }
}
